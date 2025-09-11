#!/usr/bin/env python3
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

from io import BytesIO
import json
import logging
import click

from impacket.dcerpc.v5.dcom import wmi
from impacket.dcerpc.v5.dcomrt import DCOMConnection
from impacket.dcerpc.v5.dtypes import NULL
from impacket.examples import logger


@click.command()
@click.argument(
    "target",
)
@click.option(
    "--output",
    default="processes.json",
    help="Output file.",
    type=click.File("w"),
)
@click.option("--domain", help="domain", default="")
@click.option("--username", help="username", default="")
@click.option("--password", help="password", default="")
@click.option("--nt", help="nt", default="")
@click.option(
    "--load-owners",
    default=False,
    help="Load process owner.",
    is_flag=True,
)
def list_processes(
    target: str,
    output: BytesIO,
    domain: str,
    username: str,
    password: str,
    nt: str,
    load_owners: bool,
) -> None:
    logger.init()
    logging.getLogger().setLevel(logging.INFO)
    click.echo(f"Connecting to {target} with user: {username}")
    try:
        dcom = DCOMConnection(
            target=target,
            username=username,
            password=password,
            domain=domain,
            lmhash="",
            nthash=nt,
            oxidResolver=True,
        )

        iInterface = dcom.CoCreateInstanceEx(
            wmi.CLSID_WbemLevel1Login, wmi.IID_IWbemLevel1Login
        )
        click.echo("Connected!")
        iWbemLevel1Login = wmi.IWbemLevel1Login(iInterface)
        iWbemServices = iWbemLevel1Login.NTLMLogin("//./root/cimv2", NULL, NULL)

        iWbemLevel1Login.RemRelease()
        # "Select Name, Description, ExecutablePath, ProcessId, ParentProcessId, CommandLine FROM Win32_Process"
        iEnumWbemClassObject = iWbemServices.ExecQuery(
            "Select Name, Description, ExecutablePath, ProcessId, ParentProcessId, CommandLine, Handle FROM Win32_Process"
        )
        results = []
        while True:
            try:
                pEnum = iEnumWbemClassObject.Next(0xFFFFFFFF, 1)[0]
                record = pEnum.getProperties()
                result = dict(user="")
                for key, value in record.items():
                    result[key.lower()] = value["value"]
                if load_owners and result.get("name", "") != "lsass.exe":
                    try:
                        owner = pEnum.GetOwner()
                        if owner:
                            props = owner.getProperties()
                            try:
                                user = props["User"]["value"]
                                domain = props["Domain"]["value"]
                                if user and domain:
                                    result["user"] = f"{user}@{domain}"
                            except KeyError:
                                pass
                    except Exception as e:
                        click.echo(f"Error retrieving owner: {e}")

                results.append(result)
                if len(results) % 10 == 0:
                    click.echo(f"Processes retrieved: {len(results)}")
            except Exception as e:
                if str(e).find("S_FALSE") < 0:
                    raise
                else:
                    break
        iEnumWbemClassObject.RemRelease()

        json.dump(dict(target=target, data=results), fp=output)

        click.echo(f"Retrieved {len(results)} processes from {target}")

        iWbemServices.RemRelease()
        dcom.disconnect()
    except Exception as e:
        logging.error(str(e))
        import traceback

        traceback.print_exc()
        try:
            dcom.disconnect()
        except:
            pass


if __name__ == "__main__":
    list_processes()
