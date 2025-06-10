import functools
import inspect
import json
import logging
from typing import Any, Awaitable, Callable, Optional, Type, TypeVar
from harbinger.database.redis_pool import redis_no_decode as redis

from pydantic import BaseModel, ValidationError
from typing import (Any, AsyncContextManager, Awaitable, Callable, Optional, Type,
                    TypeVar)

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
import functools
import inspect
import json
import logging
from typing import (Any, Awaitable, Callable, Optional, Type, TypeVar,
                    Concatenate, ParamSpec) # Added Concatenate, ParamSpec

# Assuming these imports are correctly set up from your project structure
from harbinger.database.redis_pool import redis_no_decode as redis
from neo4j import AsyncSession as Neo4jAsyncSession
from redis.exceptions import RedisError


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('uvicorn.error')

# Define generics FIRST
SchemaType = TypeVar("SchemaType", bound=BaseModel)
P = ParamSpec("P")

# --- Type Hints ---

# Type hint for the session factory (remains the same)
SessionFactoryType = Callable[[], AsyncContextManager[AsyncSession]]

# Type hint for the original function passed to @redis_cache (session-managing)
# Accepts db + other args (P), returns Optional[Any] model
OriginalCacheFuncType = Callable[Concatenate[AsyncSession, P], Awaitable[Optional[Any]]]

# Type hint for the wrapped function returned by @redis_cache (session-managing)
# Accepts only other args (P), returns Optional[Specific SchemaType]
WrappedCacheFuncType = Callable[P, Awaitable[Optional[SchemaType]]]

OriginalUpdateFuncType = Callable[Concatenate[AsyncSession, P], Awaitable[Optional[Any]]]
WrappedUpdateFuncType = Callable[Concatenate[AsyncSession, P], Awaitable[Optional[SchemaType]]]

def redis_cache(
    key_prefix: str,
    session_factory: SessionFactoryType,
    schema: Type[SchemaType], # The Type[SchemaType] binds the specific schema
    key_param_name: str,
    ttl_seconds: int
    # The return type uses the generics P and SchemaType directly
    # It returns a function that takes an OriginalCacheFuncType[P]
    # and returns a WrappedCacheFuncType[P, SchemaType]
) -> Callable[[OriginalCacheFuncType[P]], WrappedCacheFuncType[P, SchemaType]]:

    """
    Decorator factory for caching async function results in Redis.

    Assumes the decorated function returns a SQLAlchemy model (or similar object
    compatible with schema.model_validate/from_orm) or None.

    The decorator handles:
    - Checking Redis cache first.
    - Calling the original function on cache miss.
    - Converting the function's result to the specified Pydantic schema.
    - Storing the Pydantic schema representation (as JSON) in Redis.
    - Returning the Pydantic schema object.

    Args:
        redis: The asynchronous Redis client instance (aioredis).
        key_prefix: A prefix for the Redis cache key (e.g., 'c2implant').
        schema: The Pydantic schema class to validate/convert the result to.
        key_param_name: The name of the function parameter holding the unique ID for the key.
        ttl_seconds: Cache expiration time in seconds.

    Returns:
        A decorator function.
    """
    def decorator(func: OriginalCacheFuncType[P]) -> WrappedCacheFuncType[P, SchemaType]:
        # Ensure the original function's first parameter is 'db' or similar (optional check)
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        if not params or params[0] != 'db': # Assuming 'db' is the conventional name
             logger.warning(f"Function {func.__name__} decorated with session-managing redis_cache "
                            f"does not seem to have 'db' as its first parameter. Ensure it expects "
                            f"an AsyncSession as the first argument.")

        @functools.wraps(func) # Preserves original function metadata (name, docstring)
        async def wrapper(*args: Any, **kwargs: Any) -> Optional[SchemaType]:
            # Find the value of the key parameter from the arguments
            key_value = None
            try:
                 # Attempt to find the key in kwargs first
                 key_value = kwargs.get(key_param_name)
                 if key_value is None:
                     # If not in kwargs, find its position in the original func signature (excluding db)
                     key_param_index = -1
                     original_params = list(sig.parameters.keys())
                     try:
                          # Find index skipping the first param ('db')
                          key_param_index = original_params[1:].index(key_param_name)
                     except ValueError:
                          pass # Not found as positional arg either

                     if key_param_index != -1 and key_param_index < len(args):
                          key_value = args[key_param_index]

            except Exception as e:
                 logger.error(f"Error extracting key param '{key_param_name}' for {func.__name__}: {e}")
                 # Decide how to handle: error, skip cache, etc. Let's try calling func.
                 key_value = None # Force cache skip if key extraction fails

            if key_value is None:
                logger.warning(f"Key parameter '{key_param_name}' not found in args/kwargs for {func.__name__}. Skipping cache.")
                # Optionally raise an error or just call the function
                # Calling the function might be desired if key is sometimes optional
                async with session_factory() as db:
                    db_result = await func(db, *args, **kwargs)
                    if db_result is None:
                        return None
                    try:
                        # Still try to convert to schema if result is not None
                        return schema.model_validate(db_result) # Pydantic V2
                        # return schema.from_orm(db_result) # Pydantic V1
                    except Exception as e:
                        logger.error(f"Failed to convert result to schema {schema.__name__} for uncached call: {e}")
                        return None # Or re-raise

            # Prepare cache key
            key_value_str = str(key_value) # Handle UUIDs etc.
            cache_key = f"{key_prefix}:{key_value_str}"

            # 1. Check cache
            try:
                cached_data = await redis.get(cache_key)
                if cached_data:
                    logger.info(f"Cache HIT for key: {cache_key}")
                    try:
                        # Deserialize JSON from cache and validate with Pydantic
                        return schema.model_validate_json(cached_data) # Pydantic V2
                        # return schema.parse_raw(cached_data) # Pydantic V1
                    except (json.JSONDecodeError, ValidationError) as e:
                        logger.error(f"Failed to load/validate cached data for {cache_key}: {e}")
                        # Treat as cache miss if data is corrupted
            except RedisError as e:
                logger.error(f"Redis GET error for key {cache_key}: {e}. Falling back to function call.")

            # 2. Cache Miss: Call original function
            logger.debug(f"Cache MISS for key: {cache_key}. Calling {func.__name__}.")
            async with session_factory() as db:
                db_result = await func(db, *args, **kwargs)

                if db_result is None:
                    logger.info(f"{func.__name__} returned None for key value {key_value_str}.")
                    return None # Not found, return None, don't cache absence by default

                # 3. Convert DB model to Pydantic schema
                try:
                    schema_result = schema.model_validate(db_result) # Pydantic V2
                    # schema_result = schema.from_orm(db_result) # Pydantic V1
                except Exception as e:
                    logger.warning(f"Failed to convert DB result to schema {schema.__name__} for key {cache_key}: {e}")
                    # Decide whether to return None or the original db_result (if possible) or raise
                    return None # Safest option is often to return None if conversion fails

            # 4. Cache the Pydantic schema result
            try:
                # Serialize Pydantic schema to JSON
                data_to_cache = schema_result.model_dump_json() # Pydantic V2
                # data_to_cache = schema_result.json() # Pydantic V1

                await redis.set(cache_key, data_to_cache, ex=ttl_seconds)
                logger.debug(f"Cached data for key: {cache_key} with TTL: {ttl_seconds}s")
            except RedisError as e:
                logger.error(f"Redis SET error for key {cache_key}: {e}")
            except Exception as e:
                 logger.error(f"Failed to serialize schema {schema.__name__} for caching key {cache_key}: {e}")

            # 5. Return Pydantic schema
            return schema_result
        return wrapper
    return decorator


# # Apply the decorator
# @redis_cache(
#     key_prefix="c2implant",
#     session_factory=SessionLocal,
#     schema=schemas.C2Implant,
#     key_param_name="c2_implant_id", # Name of the ID parameter in the decorated function
#     ttl_seconds=3600  # Cache for 1 hour
# )
# async def get_c2_implant_from_db(
#     db: AsyncSession, c2_implant_id: str | uuid.UUID
# ) -> Optional[models.C2Implant]:
#     """
#     Original function: Fetches a C2Implant directly from the database.
#     Returns the SQLAlchemy model instance or None.
#     (This function's return type is models.C2Implant, but the decorator
#      will ensure the caller receives schemas.C2Implant)
#     """
#     logger.info(f"DB QUERY: Fetching C2Implant with id {c2_implant_id}")
#     return await crud.get_c2_implant(db, c2_implant_id=c2_implant_id)



# --- REVISED: Decorator for Updating Cache (db passed in) ---

def redis_cache_update(
    key_prefix: str,
    schema: Type[SchemaType], # The Pydantic schema for validation/return type
    key_param_name: str, # The name of the parameter holding the ID of the object being updated
    ttl_seconds: int # TTL for the updated cache entry
) -> Callable[[OriginalUpdateFuncType], WrappedUpdateFuncType]:
    """
    Decorator factory for updating an item in the database and then
    updating its corresponding entry in the Redis cache.

    Assumes the decorated function:
    1. Accepts an AsyncSession (`db`) as its FIRST argument.
    2. Performs a database update operation.
    3. Returns the *updated* SQLAlchemy model instance (or similar object
       compatible with schema.model_validate) or None if the update fails.

    The decorator handles:
    - Calling the original update function with the provided `db` session and arguments.
    - Taking the returned updated object.
    - Converting the updated object to the specified Pydantic schema.
    - Storing the *new* Pydantic schema representation (as JSON) in Redis,
      overwriting the previous entry.
    - Returning the Pydantic schema object representing the *updated* state.

    Args:
        key_prefix: A prefix for the Redis cache key (e.g., 'c2implant').
        schema: The Pydantic schema class to validate/convert the result to.
        key_param_name: The name of the function parameter (excluding 'db')
                        holding the unique ID of the object being updated.
        ttl_seconds: Cache expiration time in seconds for the *updated* entry.

    Returns:
        A decorator function.
    """
    def decorator(func: OriginalUpdateFuncType) -> WrappedUpdateFuncType:
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        # Verify 'db' is likely the first parameter
        if not params or params[0] != 'db': # A check for convention
             logger.warning(f"Function {func.__name__} decorated with redis_cache_update "
                            f"does not seem to have 'db' as its first parameter. Ensure it expects "
                            f"an AsyncSession as the first argument.")

        @functools.wraps(func)
        # The wrapper now explicitly accepts 'db' as the first argument
        async def wrapper(db: AsyncSession, *args: P.args, **kwargs: P.kwargs) -> Optional[SchemaType]:
            # --- Extract the Key Value ---
            # Note: key_param_name should NOT be 'db'
            key_value = None
            key_value_str = None # Initialize
            bound_args = None
            try:
                # Bind the passed arguments (excluding db) to the original function's signature
                # to easily access parameters by name, whether passed positionally or by keyword.
                # We skip the first parameter ('db') when binding args/kwargs.
                bound_args = sig.bind_partial(None, *args, **kwargs) # Use bind_partial before applying defaults
                bound_args.apply_defaults()
                # Access the key value using the name from the bound arguments
                key_value = bound_args.arguments.get(key_param_name)

            except Exception as e:
                 # This includes cases where key_param_name is not in the signature
                 # or arguments couldn't be bound correctly.
                 logger.error(f"Error binding/extracting key param '{key_param_name}' for update function {func.__name__}: {e}")
                 key_value = None

            if key_value is None and key_param_name in kwargs:
                # Fallback for simpler cases if binding fails (less robust)
                key_value = kwargs.get(key_param_name)

            # Proceed even if key extraction fails, but log inability to cache.
            can_cache = key_value is not None
            if can_cache:
                key_value_str = str(key_value)
                cache_key = f"{key_prefix}:{key_value_str}"
                logger.info(f"Preparing to update object with cache key: {cache_key}")
            else:
                logger.warning(f"Key parameter '{key_param_name}' not found or extractable for {func.__name__}. Update will proceed, but cache will not be updated.")
                cache_key = None # Ensure cache_key is None if we can't cache

            # 1. Call the original update function (MUST always be called)
            updated_db_result: Optional[Any] = None
            schema_result: Optional[SchemaType] = None
            try:
                logger.info(f"Calling update function {func.__name__}...")
                # Pass the db session along with other args/kwargs
                updated_db_result = await func(db, *args, **kwargs)

                if updated_db_result is None:
                    logger.warning(f"Update function {func.__name__} returned None. Assuming object not found or update failed.")
                    # Optional: Consider cache invalidation (delete) if this happens
                    # if can_cache and cache_key:
                    #    try:
                    #        await redis.delete(cache_key)
                    #        logger.info(f"Removed item from cache {cache_key} after update returned None.")
                    #    except RedisError as e:
                    #        logger.error(f"Redis DEL error for key {cache_key}: {e}")
                    return None

                # 2. Convert updated DB result to Pydantic schema
                try:
                    schema_result = schema.model_validate(updated_db_result)
                except Exception as e:
                    logger.error(f"Failed to convert updated DB result to schema {schema.__name__} "
                                 f"(key value: {key_value_str if can_cache else 'N/A'}): {e}")
                    # DB was updated, but conversion failed. What to return?
                    # Returning the raw result might break type hints.
                    # Returning None is ambiguous. Raising an error might be best.
                    # For now, log and return None, but consider raising.
                    return None

                # 3. Update Redis Cache (only if key was found and conversion succeeded)
                if can_cache and cache_key and schema_result:
                    try:
                        data_to_cache = schema_result.model_dump_json()
                        await redis.set(cache_key, data_to_cache, ex=ttl_seconds)
                        logger.info(f"Successfully updated cache for key: {cache_key} with TTL: {ttl_seconds}s")
                    except RedisError as e:
                        logger.error(f"Redis SET error while updating cache for key {cache_key}: {e}")
                        # Log error, but proceed to return the schema_result as DB was updated.
                    except Exception as e:
                        logger.error(f"Failed to serialize schema {schema.__name__} for caching update key {cache_key}: {e}")
                        # Log error, proceed to return schema_result.
                elif not can_cache:
                     logger.warning(f"Skipped cache update for {func.__name__} because key parameter was not found.")


                # 4. Return the Pydantic schema of the updated object
                return schema_result

            except Exception as db_update_error:
                # Catch errors from the decorated function (func) itself
                logger.error(f"Error during database update operation in {func.__name__}: {db_update_error}", exc_info=True)
                # Do NOT update the cache if the DB operation failed
                # Re-raise the error so the caller knows the update failed
                raise db_update_error

        return wrapper
    return decorator


# --- Example Usage (Updated) ---

# @redis_cache_update(
#     key_prefix="c2implant",
#     schema=schemas.C2Implant,
#     key_param_name="c2_implant_id", # Param name holding the ID (must match below, excluding 'db')
#     ttl_seconds=3600
# )
# async def update_c2_implant_in_db( # Accepts db as first argument
#     db: AsyncSession,
#     c2_implant_id: str | uuid.UUID,
#     implant_update_data: schemas.C2ImplantUpdate
# ) -> Optional[models.C2Implant]:
#     """
#     Original function: Updates a C2Implant in the database.
#     Accepts db session as the first argument.
#     Returns the *updated* SQLAlchemy model instance upon success, or None.
#     """
#     logger.info(f"DB UPDATE: Updating C2Implant with id {c2_implant_id}")
#     updated_implant = await crud.update_c2_implant(
#         db=db, # Pass the received session to CRUD
#         c2_implant_id=c2_implant_id,
#         implant=implant_update_data
#     )
#     return updated_implant


# Type hint for the original function - MUST accept db as first arg. Return type doesn't matter for decorator.
OriginalInvalidateFuncType = Callable[Concatenate[AsyncSession, P], Awaitable[Any]]
# Type hint for the wrapped function - also accepts db as first arg, returns original func's return type
WrappedInvalidateFuncType = Callable[Concatenate[AsyncSession, P], Awaitable[Any]]


# --- REVISED: Decorator for Invalidating Cache on Update/Delete ---

def redis_cache_invalidate(
    key_prefix: str,
    # schema: Type[SchemaType], # Schema is less critical now, but kept for consistency
    key_param_name: str, # The name of the parameter holding the ID of the object being modified
) -> Callable[[OriginalInvalidateFuncType], WrappedInvalidateFuncType]:
    """
    Decorator factory for invalidating (deleting) an item from the Redis
    cache after a successful database modification (update/delete).

    Assumes the decorated function:
    1. Accepts an AsyncSession (`db`) as its FIRST argument.
    2. Performs a database update or delete operation.
    3. May or may not return a value. The return value is passed through.

    The decorator handles:
    - Extracting the ID of the object being modified using `key_param_name`.
    - Calling the original database modification function.
    - If the function executes successfully *and* the ID was found,
      it deletes the corresponding cache key (`key_prefix`:`id`) from Redis.
    - Propagating any exception raised by the decorated function.
    - Returning the original function's return value.

    Args:
        key_prefix: A prefix for the Redis cache key (e.g., 'c2implant').
        # schema: The Pydantic schema class (Optional, less critical for invalidation).
        key_param_name: The name of the function parameter (excluding 'db')
                        holding the unique ID of the object being modified.

    Returns:
        A decorator function.
    """
    def decorator(func: OriginalInvalidateFuncType) -> WrappedInvalidateFuncType:
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        # Verify 'db' is likely the first parameter
        if not params or params[0] != 'db':
             logger.warning(f"Function {func.__name__} decorated with redis_cache_invalidate "
                            f"does not seem to have 'db' as its first parameter. Ensure it expects "
                            f"an AsyncSession as the first argument.")

        @functools.wraps(func)
        # The wrapper accepts 'db' as the first argument
        async def wrapper(db: AsyncSession, *args: P.args, **kwargs: P.kwargs) -> Any: # Return Any
            # --- Extract the Key Value ---
            key_value = None
            key_value_str = None
            cache_key = None
            can_invalidate = False
            try:
                bound_args = sig.bind_partial(None, *args, **kwargs)
                bound_args.apply_defaults()
                key_value = bound_args.arguments.get(key_param_name)

                if key_value is not None:
                    key_value_str = str(key_value)
                    cache_key = f"{key_prefix}:{key_value_str}"
                    can_invalidate = True
                    logger.info(f"Cache invalidation check for key: {cache_key} on call to {func.__name__}")
                else:
                     logger.warning(f"Key parameter '{key_param_name}' not found or None for {func.__name__}. Cannot invalidate cache.")

            except Exception as e:
                 logger.error(f"Error binding/extracting key param '{key_param_name}' for {func.__name__}: {e}. Cannot invalidate cache.")
                 can_invalidate = False

            # Call the original function regardless of key extraction success
            try:
                # Execute the actual DB operation
                db_result = await func(db, *args, **kwargs)

                # If the function succeeded AND we identified a cache key, invalidate it.
                if can_invalidate and cache_key:
                    try:
                        delete_count = await redis.delete(cache_key)
                        if delete_count > 0:
                            logger.info(f"Successfully invalidated cache key: {cache_key}")
                        else:
                            logger.info(f"Cache key {cache_key} not found for invalidation (or already deleted).")
                    except RedisError as e:
                        logger.error(f"Redis DEL error while invalidating cache key {cache_key}: {e}")
                        # Log error, but proceed as the main DB operation succeeded.

                # Return the original result, whether cache was invalidated or not
                return db_result

            except Exception as db_op_error:
                # Catch errors from the decorated function (func) itself
                logger.error(f"Error during database operation in {func.__name__} (key: {key_value_str if can_invalidate else 'N/A'}): {db_op_error}", exc_info=True)
                # Do NOT invalidate the cache if the DB operation failed
                # Re-raise the error so the caller knows the operation failed
                raise db_op_error

        return wrapper
    return decorator


async def invalidate_cache_entry(key_prefix: str, key_value: Any) -> bool:
    """
    Explicitly invalidates (deletes) a single entry from the Redis cache.

    Args:
        key_prefix: The prefix used for the cache key (e.g., 'c2implant', 'host').
        key_value: The unique ID (str, UUID, int, etc.) of the item to invalidate.
                   It will be converted to a string.

    Returns:
        bool: True if the key was found and deleted, False otherwise (including errors).
    """
    if key_value is None:
        logger.warning(f"Attempted to invalidate cache for prefix '{key_prefix}' with None key_value. Aborting.")
        return False

    try:
        key_value_str = str(key_value)
        cache_key = f"{key_prefix}:{key_value_str}"
        logger.info(f"Attempting to explicitly invalidate cache key: {cache_key}")

        delete_count = await redis.delete(cache_key)

        if delete_count > 0:
            logger.info(f"Successfully invalidated cache key: {cache_key}")
            return True
        else:
            logger.info(f"Cache key {cache_key} not found for invalidation.")
            return False
    except RedisError as e:
        logger.error(f"Redis DELETE error while invalidating cache key {cache_key}: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error during cache invalidation for prefix '{key_prefix}', key '{key_value}': {e}", exc_info=True)
        return False


OriginalFixedKeyFuncType = Callable[[AsyncSession], Awaitable[Any]]
# Type hint for the wrapped function (takes nothing, returns SchemaType)
WrappedFixedKeyFuncType = Callable[[], Awaitable[Optional[SchemaType]]]


def redis_cache_fixed_key(
    cache_key: str, # The exact key to use in Redis
    session_factory: SessionFactoryType,
    schema: Type[SchemaType], # Pydantic schema for validation/return
    ttl_seconds: int = 1 * 60,
) -> Callable[[OriginalFixedKeyFuncType], WrappedFixedKeyFuncType]:
    """
    Decorator factory for caching async function results with a fixed Redis key.

    Suitable for functions that compute global state or aggregates (like statistics)
    and don't rely on specific ID parameters for caching.

    Assumes the decorated function:
    - Takes only an AsyncSession (`db`) as an argument.
    - Returns an object compatible with schema.model_validate or None.

    The decorator handles:
    - Using the provided `cache_key` directly for Redis operations.
    - Checking Redis cache first.
    - Calling the original function on cache miss (managing the DB session).
    - Converting the function's result to the specified Pydantic schema.
    - Storing the Pydantic schema representation (as JSON) in Redis.
    - Returning the Pydantic schema object.

    Args:
        cache_key: The exact string to use as the Redis key.
        session_factory: Callable returning an async DB session context manager.
        schema: The Pydantic schema class to validate/convert the result to.
        ttl_seconds: Cache expiration time in seconds.

    Returns:
        A decorator function.
    """
    def decorator(func: OriginalFixedKeyFuncType) -> WrappedFixedKeyFuncType:
        # Ensure the original function's first parameter is 'db'
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        if not params or params[0] != 'db' or len(params) > 1:
             logger.warning(f"Function {func.__name__} decorated with fixed-key cache "
                            f"should ideally only accept 'db' as an argument. Found: {params}")

        @functools.wraps(func)
        async def wrapper() -> Optional[SchemaType]: # Wrapper takes no arguments directly
            # 1. Check cache using the fixed key
            try:
                cached_data = await redis.get(cache_key)
                if cached_data:
                    logger.debug(f"Cache HIT for fixed key: {cache_key}")
                    try:
                        # Deserialize JSON and validate with Pydantic
                        return schema.model_validate_json(cached_data) # Pydantic V2
                        # return schema.parse_raw(cached_data) # Pydantic V1
                    except (json.JSONDecodeError, ValidationError) as e:
                        logger.error(f"Failed to load/validate cached data for fixed key {cache_key}: {e}")
                        # Treat as cache miss
            except RedisError as e:
                logger.error(f"Redis GET error for fixed key {cache_key}: {e}. Falling back.")

            # 2. Cache Miss: Call original function
            logger.debug(f"Cache MISS for fixed key: {cache_key}. Calling {func.__name__}.")
            schema_result: Optional[SchemaType] = None
            try:
                async with session_factory() as db:
                    db_result = await func(db) # Call original func with only db

                    if db_result is None:
                        logger.info(f"{func.__name__} returned None for fixed key {cache_key}.")
                        # Decide if you want to cache None. Usually not for stats.
                        return None

                    # 3. Convert result to Pydantic schema
                    try:
                        schema_result = schema.model_validate(db_result) # Pydantic V2
                        # schema_result = schema.from_orm(db_result) # Pydantic V1
                    except Exception as e:
                        logger.error(f"Failed to convert result to schema {schema.__name__} for fixed key {cache_key}: {e}")
                        return None # Return None if conversion fails

            except Exception as call_exc:
                 logger.error(f"Error executing function {func.__name__} for fixed key {cache_key}: {call_exc}", exc_info=True)
                 # Don't cache if the function itself failed
                 raise call_exc # Re-raise the original error

            # 4. Cache the Pydantic schema result (only if successful)
            if schema_result is not None:
                try:
                    data_to_cache = schema_result.model_dump_json() # Pydantic V2
                    # data_to_cache = schema_result.json() # Pydantic V1

                    await redis.set(cache_key, data_to_cache, ex=ttl_seconds)
                    logger.debug(f"Cached data for fixed key: {cache_key} with TTL: {ttl_seconds}s")
                except RedisError as e:
                    logger.error(f"Redis SET error for fixed key {cache_key}: {e}")
                except Exception as e:
                    logger.error(f"Failed to serialize schema {schema.__name__} for caching fixed key {cache_key}: {e}")

            # 5. Return Pydantic schema
            return schema_result
        return wrapper
    return decorator


# Type hint for the Neo4j session factory function
Neo4jSessionFactoryType = Callable[[], AsyncContextManager[Neo4jAsyncSession]]

# Type hint for the original function being decorated
# It MUST accept a Neo4j AsyncSession as its first (and likely only) argument
OriginalNeo4jFuncType = Callable[[Neo4jAsyncSession], Awaitable[Any]]

# Type hint for the wrapped function returned by the decorator
# It takes NO arguments, as the decorator manages the session
WrappedNeo4jFuncType = Callable[[], Awaitable[Optional[SchemaType]]]


# --- NEW DECORATOR: redis_cache_neo4j_cm_fixed_key ---

def redis_cache_neo4j_cm_fixed_key(
    cache_key: str,                     # The exact key to use in Redis
    session_factory: Neo4jSessionFactoryType, # Function providing the Neo4j session context manager
    schema: Type[SchemaType],           # Pydantic schema for validation/return
    ttl_seconds: int = 1 * 60,
) -> Callable[[OriginalNeo4jFuncType], WrappedNeo4jFuncType]:
    """
    Decorator factory caches async Neo4j results with a fixed key, managing
    the Neo4j session internally via a context manager factory.

    Suitable for functions computing global state or aggregates from Neo4j
    (e.g., statistics).

    Assumes the decorated function:
    - Accepts a neo4j.AsyncSession as its FIRST argument.
    - Returns an object compatible with schema.model_validate or None.

    The decorator handles:
    - Checking Redis cache using `cache_key`.
    - On cache miss: creates a Neo4j session using `session_factory`,
      calls the original function with the session.
    - Converts the result to the Pydantic `schema`.
    - Caches the Pydantic object as JSON in Redis.
    - Returns the Pydantic object.

    Args:
        cache_key: The exact string to use as the Redis key.
        session_factory: Callable returning an async Neo4j session context manager.
        schema: The Pydantic schema class to validate/convert the result to.
        ttl_seconds: Cache expiration time in seconds.

    Returns:
        A decorator function.
    """
    def decorator(func: OriginalNeo4jFuncType) -> WrappedNeo4jFuncType:
        # Optional: Check signature of the original function
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        # Verify it takes at least one argument (the session)
        if not params:
             logger.error(f"Function {func.__name__} decorated with Neo4j session-managed cache "
                           f"must accept a Neo4j AsyncSession argument, but takes none.")
             # You might want to raise an error here instead of just warning
        elif len(params) > 1:
             logger.warning(f"Function {func.__name__} decorated with Neo4j session-managed cache "
                            f"should ideally accept only one argument (the session). Found: {params}")
        # You could add a check for param name convention (e.g., 'session') if desired

        @functools.wraps(func)
        # Wrapper takes no arguments - session is managed internally
        async def wrapper() -> Optional[SchemaType]:
            # 1. Check cache using the fixed key
            try:
                cached_data = await redis.get(cache_key)
                if cached_data:
                    logger.debug(f"Cache HIT for Neo4j fixed key: {cache_key}")
                    try:
                        # Deserialize JSON and validate with Pydantic
                        return schema.model_validate_json(cached_data) # Pydantic V2
                    except (json.JSONDecodeError, ValidationError) as e:
                        logger.error(f"CACHE CORRUPTION: Failed to load/validate cached data for Neo4j fixed key {cache_key}: {e}")
                        # Treat as cache miss
            except RedisError as e:
                logger.error(f"REDIS ERROR (GET): Failed for Neo4j key {cache_key}: {e}. Falling back to DB.")
            except Exception as e:
                logger.error(f"UNEXPECTED ERROR during cache check for {cache_key}: {e}", exc_info=True)


            # 2. Cache Miss: Create session and call original function
            logger.debug(f"Cache MISS for Neo4j fixed key: {cache_key}. Calling {func.__name__}.")
            schema_result: Optional[SchemaType] = None
            try:
                # Create Neo4j session using the provided factory
                async with session_factory() as session:
                    # Call original func with the created session
                    db_result = await func(session) # Pass the session here

                    if db_result is None:
                        logger.info(f"{func.__name__} returned None for Neo4j fixed key {cache_key}. Result not cached.")
                        # Return None, don't attempt to cache absence for stats
                        return None

                    # 3. Convert result to Pydantic schema
                    try:
                        schema_result = schema.model_validate(db_result) # Pydantic V2
                    except Exception as e:
                        logger.error(f"SCHEMA VALIDATION FAILED: Could not convert Neo4j result from {func.__name__} "
                                     f"to schema {schema.__name__} for fixed key {cache_key}: {e}")
                        # Decide whether to raise or return None. Returning None prevents caching bad data.
                        return None

            except Exception as call_exc:
                 # This includes errors during session creation or func execution
                 logger.error(f"NEO4J/FUNCTION ERROR: Failed during session creation or execution of {func.__name__} "
                              f"for fixed key {cache_key}: {call_exc}", exc_info=True)
                 # Don't cache if the function itself failed. Re-raise to be caught by outer handlers (like @exception_handler)
                 raise call_exc

            # 4. Cache the Pydantic schema result (only if successful)
            if schema_result is not None:
                try:
                    data_to_cache = schema_result.model_dump_json() # Pydantic V2
                    await redis.set(cache_key, data_to_cache, ex=ttl_seconds)
                    logger.debug(f"Cached Neo4j data for fixed key: {cache_key} with TTL: {ttl_seconds}s")
                except RedisError as e:
                    logger.error(f"REDIS ERROR (SET): Failed for Neo4j key {cache_key}: {e}")
                    # Log error, but still return the result obtained from DB
                except Exception as e:
                    logger.error(f"SERIALIZATION ERROR: Failed to serialize schema {schema.__name__} "
                                 f"for caching Neo4j fixed key {cache_key}: {e}")
                    # Log error, but still return the result obtained from DB

            # 5. Return Pydantic schema result (even if caching failed)
            return schema_result
        return wrapper
    return decorator
