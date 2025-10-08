# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib
import os
import re

from harbinger import models
from jinja2.sandbox import SandboxedEnvironment
from sqlalchemy.orm.decl_api import DeclarativeMeta

database_objects = {
    name: cls
    for name, cls in models.__dict__.items()
    if type(cls) == DeclarativeMeta and name != "Base" and name != "TimeLine"
}

env = SandboxedEnvironment(
    enable_async=False,
    autoescape=False,
)

type_map = {
    "UUID": "str | UUID4",
    "VARCHAR": "str",
    "BOOLEAN": "bool",
    "INTEGER": "int",
    "BIGINT": "int",
    "TIMESTAMP": "str",
    "JSON": "str",
    "DATETIME": "datetime",
    "ARRAY": "list[str]",
    "BLOB": "bytes",
}

ts_type_map = {
    "UUID": "string",
    "VARCHAR": "string",
    "BOOLEAN": "boolean",
    "INTEGER": "number",
    "BIGINT": "number",
    "TIMESTAMP": "string",
    "DATETIME": "string",
    "ARRAY": "Array<string>",
}

for name in database_objects:
    print(f"Processing {name}")
    name_vue = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    route = name_vue + "s"

    os.makedirs(f"gen/{name}", exist_ok=True)
    obj = database_objects[name]
    filters = []
    names = []

    ts_fields = []

    for column in obj.__table__.columns:  # type: ignore
        # print(column, str(column.type), column.name)
        column_type = str(column.type)
        if "(" in column_type:
            column_type = column_type.split("(")[0]

        with contextlib.suppress(KeyError):
            ts_fields.append({"name": column.name, "value": ts_type_map[column_type]})

        if column.name == "id":
            continue
        if str(column_type) == "JSON":
            continue
        if str(column_type) == "VARCHAR":
            names.append(f"{column.name}")
        filters.append({"name": column.name, "value": type_map[column_type]})

    constraint = ""
    for c in obj.__table__.constraints:  # type: ignore
        if c.name:
            constraint = c.name

    filters_template = """
# Filters.py
class {{ name }}Filter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    {% for filter in filters %}{{ filter.name }}: {{ filter.value }} | None = None
    {% endfor %}labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.{{ name }}
        search_model_fields = {{ names }}
"""
    templ = env.from_string(filters_template)
    resp = templ.render(
        name=name,
        filters=filters,
        names=names,
        route=route,
        constraint=constraint,
    )

    with open(f"gen/{name}/filters.py", "w") as f:
        f.write(resp)

    schemas_template = """
# Schemas.py
class {{name}}Base(BaseModel):
    {% for filter in filters %}{{ filter.name }}: {{ filter.value }} | None = None
    {% endfor %}

class {{name}}Create({{name}}Base):
    pass

class {{name}}Update({{name}}Base):
    pass

class {{name}}Created({{name}}Base):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

class {{name}}({{name}}Base):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

    labels: List["Label"] | None = None
"""
    templ = env.from_string(schemas_template)
    resp = templ.render(
        name=name,
        filters=filters,
        names=names,
        route=route,
        constraint=constraint,
    )

    with open(f"gen/{name}/schemas.py", "w") as f:
        f.write(resp)

    router_schema = """
# ROUTER
@router.get(
    "/{{route}}/",
    response_model=Page[schemas.{{name}}],
    tags=["crud", "{{route}}"],
)
async def list_{{route}}(
    filters: filters.{{name}}Filter = FilterDepends(filters.{{name}}Filter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user)
):
    return await crud.get_{{route}}_paged(db, filters)


@router.get(
    "/{{route}}/filters", response_model=list[schemas.Filter], tags=["{{route}}", "crud"]
)
async def {{route}}_filters(
    filters: filters.{{name}}Filter = FilterDepends(filters.{{name}}Filter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_{{route}}_filters(
        db,
        filters,
    )


@router.get(
    "/{{route}}/{id}",
    response_model=Optional[schemas.{{name}}],
    tags=["crud", "{{route}}"],
)
async def get_{{route[:-1]}}(
    id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_{{route[:-1]}}(db, id)


@router.post("/{{route}}/", response_model=schemas.{{name}}Created, tags=["crud", "{{route}}"])
async def create_{{route[:-1]}}(
    {{route}}: schemas.{{name}}Create,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    _, resp = await crud.create_{{route}}(db, {{route}})
    return resp

@router.put(
    "/{{route}}/{id}",
    response_model=Optional[schemas.{{name}}],
    tags=["crud", "{{route}}"],
)
async def update_{{route[:-1]}}(
    id: UUID4,
    {{route}}: schemas.{{name}}Update,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_{{route}}(db, id, {{route}})
"""
    templ = env.from_string(router_schema)
    resp = templ.render(
        name=name,
        filters=filters,
        names=names,
        route=route,
        constraint=constraint,
    )

    with open(f"gen/{name}/router.py", "w") as f:
        f.write(resp)

    crud_schema = """
# CRUD
async def get_{{route}}_paged(
    db: AsyncSession, filters: filters.{{name}}Filter
) -> Page[models.{{name}}]:
    q: Select = select(models.{{name}})
    q = q.outerjoin(models.{{name}}.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.{{name}}.id)
    return await apaginate(db, q)


async def get_{{route}}(
    db: AsyncSession,
    filters: filters.{{name}}Filter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.{{name}}]:
    q: Select = select(models.{{name}})
    q = q.outerjoin(models.{{name}}.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_{{route}}_filters(db: AsyncSession, filters: filters.{{name}}Filter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.{{name}}.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    for field in {{names}}:
        res = await create_filter_for_column(
            db, q, getattr(models.{{name}}, field), field, field
        )
        result.append(res)

    return result

async def get_{{route}}(db: AsyncSession, id: UUID4) -> Optional[models.{{name}}]:
    return await db.get(models.{{name}}, id)

async def create_{{route[:-1]}}(db: AsyncSession, {{route}}: schemas.{{name}}Create) -> Tuple[bool, models.{{name}}]:
    data = {{route}}.model_dump()
    q = insert(models.{{name}}).values(**data).values(time_created=func.now())
    data['time_updated'] = func.now()
    update_stmt = q.on_conflict_do_update("{{constraint}}", set_=data)
    result = await db.scalars(
        update_stmt.returning(models.{{name}}),
        execution_options={"populate_existing": True},
    )
    result = result.unique().one()
    await db.refresh(result)
    await db.commit()
    return result.time_updated == None, result

async def update_{{route[:-1]}}(db: AsyncSession, id: str | uuid.UUID, {{route}}: schemas.{{name}}Update) -> None:
    q = update(models.{{name}}).where(models.{{name}}.id == id).values(**{{route}}.model_dump(exclude_unset=True, exclude_defaults=True, exclude_none=True))
    await db.execute(q)
    await db.commit()
"""
    templ = env.from_string(crud_schema)
    resp = templ.render(
        name=name,
        filters=filters,
        names=names,
        route=route,
        constraint=constraint,
    )

    with open(f"gen/{name}/crud.py", "w") as f:
        f.write(resp)

    test_template = """
    async def test_{{route}}(self):
        async with self.SessionLocal() as db:
            to_create = schemas.{{name}}Create() # TODO
            created, {{route}}1 = await crud.create_{{route[:-1]}}(db, to_create)
            self.assertTrue(created)
            created, {{route}}2 = await crud.create_{{route[:-1]}}(db, to_create)
            self.assertFalse(created)
            self.assertEqual({{route}}1.id, {{route}}2.id)
            filter_list = await crud.get_{{route}}_filters(db, filters.{{name}}Filter())
            self.assertGreater(len(filter_list), 2)
            mockdb.assert_awaited_once()
    """
    templ = env.from_string(test_template)
    resp = templ.render(
        name=name,
        filters=filters,
        names=names,
        route=route,
        constraint=constraint,
    )

    with open(f"gen/{name}/tests.py", "w") as f:
        f.write(resp)

    admin_template = """
class {{ name }}Admin(ModelView, model=models.{{ name }}):
    can_create = True
    name = "{{ name }}"
    name_plural = "{{ name }}s"
    column_list = {{ fields_short }}
    icon = "fa-solid fa-server"
"""
    templ = env.from_string(admin_template)
    resp = templ.render(
        name=name,
        filters=filters,
        names=names,
        route=route,
        constraint=constraint,
        fields_short=[name["name"] for name in ts_fields],
    )

    with open(f"gen/{name}/admin.py", "w") as f:
        f.write(resp)

    models_template = """
// models.ts
export interface {{name}} {
{% for field in ts_fields %}{{field.name}}: {{field.value}};
{%endfor%}labels: Array<Label>;
}
"""
    templ = env.from_string(models_template)
    resp = templ.render(
        name=name,
        filters=filters,
        names=names,
        route=route,
        constraint=constraint,
        ts_fields=ts_fields,
        name_vue=name_vue,
        fields_short=[name["name"] for name in ts_fields],
    )
    with open(f"gen/{name}/models.ts", "w") as f:
        f.write(resp)

    page_template = """
//{{name}}Page.vue
<template>
<q-page padding>
    <{{name_vue}}-list />
</q-page>
</template>

<script setup lang="ts">
import {{name}}List from 'src/components/{{name}}List.vue';
</script>
"""
    templ = env.from_string(page_template)
    resp = templ.render(
        name=name,
        filters=filters,
        names=names,
        route=route,
        constraint=constraint,
        ts_fields=ts_fields,
        name_vue=name_vue,
        fields_short=[name["name"] for name in ts_fields],
    )
    with open(f"gen/{name}/{name}Page.vue", "w") as f:
        f.write(resp)

    component_page = """
//src/components/{{name}}List.vue
<template>
<div>
    <q-btn color="secondary" icon="refresh" @click="store.LoadData">Refresh</q-btn>
    <q-table :rows-per-page-options="[5, 10, 15, 20, 25, 50, 100]" title="{{name}}" :rows="data" row-key="id"
    :columns="columns" :loading="loading" v-model:pagination="pagination" @request="store.onRequest"
    :visible-columns="visible">
    <template v-slot:top>
        <div class="col-2 q-table__title">{{name}}</div>
        <q-space />
        <filter-view object-type="{{route}}" v-model="filters" v-on:updateFilters="store.updateFilters" />
        <q-select v-model="visible" multiple borderless dense options-dense :display-value="$q.lang.table.columns"
        emit-value map-options :options="columns" option-value="name" style="min-width: 150px">
        <template v-slot:option="{ itemProps, opt, selected, toggleOption }">
            <q-item v-bind="itemProps">
            <q-item-section>
                <q-item-label :class="$q.dark.isActive ? 'text-white' : 'text-black'">{%raw%}{{ opt.label }}{%endraw%}</q-item-label>
            </q-item-section>
            <q-item-section side>
                <q-toggle :model-value="selected" @update:model-value="toggleOption(opt)" />
            </q-item-section>
            </q-item>
        </template>
        </q-select>
    </template>
    <template v-slot:body="props">
        <q-tr :props="props" class="cursor-pointer">
        {% for field in ts_fields %}<q-td key="{{ field.name }}" :props="props">
            {%raw%}{{ props.row.{%endraw%}{{field.name}}{%raw%} }}{%endraw%}
        </q-td>
        {% endfor %}
        <q-td key="labels" :props="props">
            <labels-list object-type="{{route}}" :object-id="String(props.row.id)" v-model="props.row.labels" />
        </q-td>
        </q-tr>
    </template>
    </q-table>
</div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { {{name}} } from 'src/models'
import { QTableProps } from 'quasar';
import LabelsList from './LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import { useCounterStore } from 'src/stores/object-counters';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'

const counter_store = useCounterStore();

counter_store.clear('{{route}}');
const visible = ref({{fields_short}})

const useStore = defineTypedStore<{{name}}>('{{route}}');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();

const columns: QTableProps['columns'] = [{% for field in ts_fields %}
{ name: '{{ field.name }}', label: '{{ field.name }}', field: '{{ field.name }}', align: 'left', sortable: false },{% endfor %}
{ name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

</script>
"""
    templ = env.from_string(component_page)
    resp = templ.render(
        name=name,
        filters=filters,
        names=names,
        route=route,
        constraint=constraint,
        ts_fields=ts_fields,
        name_vue=name_vue,
        fields_short=[name["name"] for name in ts_fields],
    )
    with open(f"gen/{name}/{name}List.vue", "w") as f:
        f.write(resp)

    add_page_template = """
//Add{{name}}.vue
<template>
<q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">

    {% for field in ts_fields %}
    <q-input filled v-model="form.{{field.name}}" label="{{field.name}}" />{% endfor %}

    <div>
    <q-btn
        label="Submit"
        type="submit"
        color="secondary"
        :loading="loading"
    />
    <q-btn
        label="Reset"
        type="reset"
        color="secondary"
        flat
        class="q-ml-sm"
    />
    </div>
</q-form>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { ref, toRefs } from 'vue';
import { api } from 'boot/axios';
import { useRouter } from 'vue-router';

const $q = useQuasar();
const loading = ref(false);
const $router = useRouter();

interface Form {
{% for field in ts_fields %}
{{field.name}}: {{field.value}};{% endfor %}
}

const form = ref<Form>({} as Form);

function onSubmit() {
    api
    .post('/{{route}}/', form.value)
    .then((response) => {
        $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        position: 'top',
        message: `Submitted, {{route}}_id: ${response.data.id}`,
        });
        $router.push({ name: '{{route}}' });
        loading.value = false;
    })
    .catch(() => {
        loading.value = false;
        $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Creation failed',
        icon: 'report_problem',
        });
    });
}

function onReset() {
form.value = {} as Form;
}
</script>
"""
    templ = env.from_string(add_page_template)
    resp = templ.render(
        name=name,
        filters=filters,
        names=names,
        route=route,
        constraint=constraint,
        ts_fields=ts_fields,
        name_vue=name_vue,
        fields_short=[name["name"] for name in ts_fields],
    )
    with open(f"gen/{name}/Add{name}.vue", "w") as f:
        f.write(resp)

    routes_template = """
// routes.ts
    {
        path: '{{route}}',
        name: '{{route}}',
        component: () => import('src/pages/{{name}}Page.vue'),
        meta: {
        icon: 'check_circle',
        parent: 'dashboard',
        display_name: '{{name}}',
        },
    },
    {
        path: 'add_{{route}}',
        name: 'add_{{route}}',
        component: () => import('src/pages/Add{{name}}.vue'),
        meta: {
        icon: 'check_circle',
        parent: '{{route}}',
        display_name: '{{name}}',
        },
    }
    """
    templ = env.from_string(routes_template)
    resp = templ.render(
        name=name,
        filters=filters,
        names=names,
        route=route,
        constraint=constraint,
        ts_fields=ts_fields,
        name_vue=name_vue,
        fields_short=[name["name"] for name in ts_fields],
    )
    with open(f"gen/{name}/routes.ts", "w") as f:
        f.write(resp)
