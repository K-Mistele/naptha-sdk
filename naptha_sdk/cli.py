import argparse
import asyncio
from dotenv import load_dotenv
from naptha_sdk.client.naptha import Naptha
from naptha_sdk.client.hub import user_setup_flow
from naptha_sdk.user import get_public_key
from naptha_sdk.schemas import AgentConfig, AgentDeployment, EnvironmentDeployment, OrchestratorDeployment, OrchestratorRunInput, EnvironmentRunInput
import os
import shlex
import yaml
import json
from tabulate import tabulate
from textwrap import wrap

load_dotenv(override=True)

def load_yaml_to_dict(file_path):
    with open(file_path, 'r') as file:
        # Load the YAML content into a Python dictionary
        yaml_content = yaml.safe_load(file)
    return yaml_content

def creds(naptha):
    return naptha.services.show_credits()

def list_services(naptha):
    services = naptha.services.list_services()
    for service in services:
        print(service) 

async def list_nodes(naptha):
    nodes = await naptha.hub.list_nodes()
    
    if not nodes:
        print("No nodes found.")
        return

    # Determine available keys
    keys = list(nodes[0].keys())

    # Create headers and table data based on available keys
    headers = keys
    table_data = []

    for node in nodes:
        row = []
        for key in keys:
            value = str(node.get(key, ''))
            if len(value) > 50:
                wrapped_value = '\n'.join(wrap(value, width=50))
                row.append(wrapped_value)
            else:
                row.append(value)
        table_data.append(row)

    print("\nAll Nodes:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\nTotal nodes: {len(nodes)}")

async def list_agents(naptha):
    agents = await naptha.hub.list_agents()
    
    if not agents:
        print("No agents found.")
        return

    headers = ["Name", "ID", "Type", "Version", "Author", "Description"]
    table_data = []

    for agent in agents:
        # Wrap the description text
        wrapped_description = '\n'.join(wrap(agent['description'], width=50))
        
        row = [
            agent['name'],
            agent['id'],
            agent['type'],
            agent['version'],
            agent['author'],
            wrapped_description
        ]
        table_data.append(row)

    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\nTotal agents: {len(agents)}")

async def list_orchestrators(naptha):
    orchestrators = await naptha.hub.list_orchestrators()
    
    if not orchestrators:
        print("No orchestrators found.")
        return

    headers = ["Name", "ID", "Type", "Version", "Author", "Description"]
    table_data = []

    for orchestrator in orchestrators:
        # Wrap the description text
        wrapped_description = '\n'.join(wrap(orchestrator['description'], width=50))
        
        row = [
            orchestrator['name'],
            orchestrator['id'],
            orchestrator['type'],
            orchestrator['version'],
            orchestrator['author'],
            wrapped_description
        ]
        table_data.append(row)

    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\nTotal orchestrators: {len(orchestrators)}")

async def list_environments(naptha):
    environments = await naptha.hub.list_environments()
    
    if not environments:
        print("No environments found.")
        return

    headers = ["Name", "ID", "Type", "Version", "Author", "Description"]
    table_data = []

    for environment in environments:
        # Wrap the description text
        wrapped_description = '\n'.join(wrap(environment['description'], width=50))
        
        row = [
            environment['name'],
            environment['id'],
            environment['type'],
            environment['version'],
            environment['author'],
            wrapped_description
        ]
        table_data.append(row)

    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\nTotal environments: {len(environments)}")

async def list_personas(naptha):
    personas = await naptha.hub.list_personas()
    
    if not personas:
        print("No personas found.")
        return

    headers = ["Name", "ID", "Version", "Author", "Description", "URL"]
    table_data = []

    for persona in personas:
        # Wrap the description text
        wrapped_description = '\n'.join(wrap(persona['description'], width=50))
        
        row = [
            persona['name'],
            persona['id'],
            persona['version'],
            persona['author'],
            wrapped_description,
            persona['url']
        ]
        table_data.append(row)

    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\nTotal personas: {len(personas)}")

async def create_agent(naptha, agent_config):
    print(f"Agent Config: {agent_config}")
    agent = await naptha.hub.create_agent(agent_config)
    if isinstance(agent, dict):
        print(f"Agent created: {agent}")
    elif isinstance(agent, list):
        print(f"Agent created: {agent[0]}")

async def create_orchestrator(naptha, orchestrator_config):
    print(f"Orchestrator Config: {orchestrator_config}")
    orchestrator = await naptha.hub.create_orchestrator(orchestrator_config)
    if isinstance(orchestrator, dict):
        print(f"Orchestrator created: {orchestrator}")
    elif isinstance(orchestrator, list):
        print(f"Orchestrator created: {orchestrator[0]}")

async def create_environment(naptha, environment_config):
    print(f"Environment Config: {environment_config}")
    environment = await naptha.hub.create_environment(environment_config)
    if isinstance(environment, dict):
        print(f"Environment created: {environment}")
    elif isinstance(environment, list):
        print(f"Environment created: {environment[0]}")

async def create_persona(naptha, persona_config):
    print(f"Persona Config: {persona_config}")
    persona = await naptha.hub.create_persona(persona_config)
    if isinstance(persona, dict):
        print(f"Persona created: {persona}")
    elif isinstance(persona, list):
        print(f"Persona created: {persona[0]}")

async def run(
    naptha, 
    module_name, 
    user_id,
    parameters=None, 
    worker_node_urls="http://localhost:7001",
    environment_node_urls=["http://localhost:7001"],
    yaml_file=None, 
    personas_urls=None
):   
    if yaml_file and parameters:
        raise ValueError("Cannot pass both yaml_file and parameters")
    
    if yaml_file:
        parameters = load_yaml_to_dict(yaml_file)

    if "orchestrator:" in module_name:
        module_type = "orchestrator"
    elif "agent:" in module_name:
        module_type = "agent" 
    elif "environment:" in module_name:
        module_type = "environment"
    else:
        module_type = "agent" # Default to agent for backwards compatibility

    user = await naptha.node.check_user(user_input={"public_key": naptha.hub.public_key})

    if user['is_registered'] == True:
        print("Found user...", user)
    else:
        print("No user found. Registering user...")
        user = await naptha.node.register_user(user_input=user)
        print(f"User registered: {user}.")

    if module_type == "agent":
        print("Running Agent...")
        agent_deployment = AgentDeployment(
            name=module_name, 
            module={"name": module_name}, 
            worker_node_url=worker_node_urls, 
            agent_config=AgentConfig(persona_module={"url": personas_urls})
        )

        agent_run_input = {
            'consumer_id': user_id,
            "inputs": parameters,
            "agent_deployment": agent_deployment.model_dump(),
            "personas_urls": personas_urls
        }
        print(f"Agent run input: {agent_run_input}")

        agent_run = await naptha.node.run_agent_and_poll(agent_run_input)

    elif module_type == "orchestrator":
        print("Running Orchestrator...")
        agent_deployments = []
        for worker_node_url in worker_node_urls:
            agent_deployments.append(AgentDeployment(worker_node_url=worker_node_url))

        environment_deployments = []
        for environment_node_url in environment_node_urls:
            environment_deployments.append(EnvironmentDeployment(environment_node_url=environment_node_url))

        orchestrator_deployment = OrchestratorDeployment(
            name=module_name, 
            module={"name": module_name}, 
            orchestrator_node_url=os.getenv("NODE_URL")
        )

        orchestrator_run_input = OrchestratorRunInput(
            consumer_id=user_id,
            inputs=parameters,
            orchestrator_deployment=orchestrator_deployment,
            agent_deployments=agent_deployments,
            environment_deployments=environment_deployments
        )

        orchestrator_run = await naptha.node.run_orchestrator_and_poll(orchestrator_run_input)

    elif module_type == "environment":
        print("Running Environment...")

        environment_deployment = EnvironmentDeployment(
            name=module_name, 
            module={"name": module_name}, 
            environment_node_url=environment_node_urls[0]
        )

        environment_run_input = EnvironmentRunInput(
            inputs=parameters,
            environment_deployment=environment_deployment,
            consumer_id=user_id,
        )
        environment_run = await naptha.node.run_environment_and_poll(environment_run_input)
        
async def read_storage(naptha, hash_or_name, output_dir='./files', ipfs=False):
    """Read from storage, IPFS, or IPNS."""
    try:
        await naptha.node.read_storage(hash_or_name.strip(), output_dir, ipfs=ipfs)
    except Exception as err:
        print(f"Error: {err}")


async def write_storage(naptha, storage_input, ipfs=False, publish_to_ipns=False, update_ipns_name=None):
    """Write to storage, optionally to IPFS and/or IPNS."""
    try:
        response = await naptha.node.write_storage(storage_input, ipfs=ipfs, publish_to_ipns=publish_to_ipns, update_ipns_name=update_ipns_name)
        print(response)
    except Exception as err:
        print(f"Error: {err}")

async def main():
    public_key = get_public_key(os.getenv("PRIVATE_KEY")) if os.getenv("PRIVATE_KEY") else None
    hub_username = os.getenv("HUB_USER")
    hub_password = os.getenv("HUB_PASS")
    hub_url = os.getenv("HUB_URL")

    naptha = Naptha()

    parser = argparse.ArgumentParser(description="CLI with for Naptha")
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # Node commands
    nodes_parser = subparsers.add_parser("nodes", help="List available nodes.")

    # Agent commands
    agents_parser = subparsers.add_parser("agents", help="List available agents.")
    agents_parser.add_argument('agent_name', nargs='?', help='Optional agent name')
    agents_parser.add_argument("-p", '--parameters', type=str, help='Parameters in "key=value" format')
    agents_parser.add_argument('-d', '--delete', action='store_true', help='Delete a agent')

    # Orchestrator commands
    orchestrators_parser = subparsers.add_parser("orchestrators", help="List available orchestrators.")
    orchestrators_parser.add_argument('orchestrator_name', nargs='?', help='Optional orchestrator name')
    orchestrators_parser.add_argument("-p", '--parameters', type=str, help='Parameters in "key=value" format')
    orchestrators_parser.add_argument('-d', '--delete', action='store_true', help='Delete an orchestrator')

    # Environment commands
    environments_parser = subparsers.add_parser("environments", help="List available environments.")
    environments_parser.add_argument('environment_name', nargs='?', help='Optional environment name')
    environments_parser.add_argument("-p", '--parameters', type=str, help='Parameters in "key=value" format')
    environments_parser.add_argument('-d', '--delete', action='store_true', help='Delete an environment')

    # Persona commands
    personas_parser = subparsers.add_parser("personas", help="List available personas.")
    personas_parser.add_argument('persona_name', nargs='?', help='Optional persona name')
    personas_parser.add_argument("-p", '--parameters', type=str, help='Parameters in "key=value" format')
    personas_parser.add_argument('-d', '--delete', action='store_true', help='Delete a persona')

    # Run command
    run_parser = subparsers.add_parser("run", help="Execute run command.")
    run_parser.add_argument("agent", help="Select the agent to run")
    run_parser.add_argument("-p", '--parameters', type=str, help='Parameters in "key=value" format')
    run_parser.add_argument("-n", "--worker_nodes", help="Worker nodes to take part in agent runs.")
    run_parser.add_argument("-e", "--environment_nodes", help="Environment nodes to store data during agent runs.")
    run_parser.add_argument("-u", "--personas_urls", help="Personas URLs to install before running the agent")
    run_parser.add_argument("-f", "--file", help="YAML file with agent run parameters")

    # Read storage commands
    read_storage_parser = subparsers.add_parser("read_storage", help="Read from storage.")
    read_storage_parser.add_argument("-id", "--agent_run_id", help="Agent run ID to read from")
    read_storage_parser.add_argument("-o", "--output_dir", default="files", help="Output directory to write to")
    read_storage_parser.add_argument("--ipfs", help="Read from IPFS", action="store_true")

    # Write storage commands
    write_storage_parser = subparsers.add_parser("write_storage", help="Write to storage.")
    write_storage_parser.add_argument("-i", "--storage_input", help="Path to file or directory to write to storage")
    write_storage_parser.add_argument("--ipfs", help="Write to IPFS", action="store_true")
    write_storage_parser.add_argument("--publish_to_ipns", help="Publish to IPNS", action="store_true")
    write_storage_parser.add_argument("--update_ipns_name", help="Update IPNS name")

    # Signup command
    signup_parser = subparsers.add_parser("signup", help="Sign up a new user.")

    # Publish command
    publish_parser = subparsers.add_parser("publish", help="Publish agents.")

    async with naptha as naptha:
        args = parser.parse_args()
        if args.command == "signup":
            _, user_id = await user_setup_flow(hub_url, public_key)
        elif args.command in ["nodes", "agents", "orchestrators", "environments", "personas", "run", "read_storage", "write_storage", "publish"]:
            if not naptha.hub.is_authenticated:
                if not hub_username or not hub_password:
                    print("Please set HUB_USER and HUB_PASS environment variables or sign up first (run naptha signup).")
                    return
                _, _, user_id = await naptha.hub.signin(hub_username, hub_password)

            if args.command == "nodes":
                await list_nodes(naptha)   
            elif args.command == "agents":
                if not args.agent_name:
                    await list_agents(naptha)
                elif args.delete and len(args.agent_name.split()) == 1:
                    await naptha.hub.delete_agent(args.agent_name)
                elif len(args.agent_name.split()) == 1:
                    if hasattr(args, 'parameters') and args.parameters is not None:
                        params = shlex.split(args.parameters)
                        parsed_params = {}
                        for param in params:
                            key, value = param.split('=')
                            parsed_params[key] = value

                        required_parameters = ['description', 'url', 'type', 'version']
                        if not all(param in parsed_params for param in required_parameters):
                            print(f"Missing one or more of the following required parameters: {required_parameters}")
                            return
                            
                        agent_config = {
                            "id": f"agent:{args.agent_name}",
                            "name": args.agent_name,
                            "description": parsed_params['description'],
                            "author": naptha.hub.user_id,
                            "url": parsed_params['url'],
                            "type": parsed_params['type'],
                            "version": parsed_params['version'],
                        }
                        await create_agent(naptha, agent_config)
                else:
                    print("Invalid command.")
            elif args.command == "orchestrators":
                if not args.orchestrator_name:
                    await list_orchestrators(naptha)
                elif args.delete and len(args.orchestrator_name.split()) == 1:
                    await naptha.hub.delete_orchestrator(args.orchestrator_name)
                elif len(args.orchestrator_name.split()) == 1:
                    if hasattr(args, 'parameters') and args.parameters is not None:
                        params = shlex.split(args.parameters)
                        parsed_params = {}
                        for param in params:
                            key, value = param.split('=')
                            parsed_params[key] = value

                        required_parameters = ['description', 'url', 'type', 'version']
                        if not all(param in parsed_params for param in required_parameters):
                            print(f"Missing one or more of the following required parameters: {required_parameters}")
                            return
                            
                        orchestrator_config = {
                            "id": f"orchestrator:{args.orchestrator_name}",
                            "name": args.orchestrator_name,
                            "description": parsed_params['description'],
                            "author": naptha.hub.user_id,
                            "url": parsed_params['url'],
                            "type": parsed_params['type'],
                            "version": parsed_params['version'],
                        }
                        await create_orchestrator(naptha, orchestrator_config)
                else:
                    print("Invalid command.")
            elif args.command == "environments":
                if not args.environment_name:
                    await list_environments(naptha)
                elif args.delete and len(args.environment_name.split()) == 1:
                    await naptha.hub.delete_environment(args.environment_name)
                elif len(args.environment_name.split()) == 1:
                    if hasattr(args, 'parameters') and args.parameters is not None:
                        params = shlex.split(args.parameters)
                        parsed_params = {}
                        for param in params:
                            key, value = param.split('=')
                            parsed_params[key] = value

                        required_parameters = ['description', 'url', 'type', 'version']
                        if not all(param in parsed_params for param in required_parameters):
                            print(f"Missing one or more of the following required parameters: {required_parameters}")
                            return
                            
                        environment_config = {
                            "id": f"environment:{args.environment_name}",
                            "name": args.environment_name,
                            "description": parsed_params['description'],
                            "author": naptha.hub.user_id,
                            "url": parsed_params['url'],
                            "type": parsed_params['type'],
                            "version": parsed_params['version'],
                        }
                        await create_environment(naptha, environment_config)
                else:
                    print("Invalid command.")
            elif args.command == "personas":
                if not args.persona_name:
                    await list_personas(naptha)
                elif args.delete and len(args.persona_name.split()) == 1:
                    await naptha.hub.delete_persona(args.persona_name)
                elif len(args.persona_name.split()) == 1:
                    if hasattr(args, 'parameters') and args.parameters is not None:
                        params = shlex.split(args.parameters)
                        parsed_params = {}
                        for param in params:
                            key, value = param.split('=')
                            parsed_params[key] = value

                        required_parameters = ['description', 'url', 'version']
                        if not all(param in parsed_params for param in required_parameters):
                            print(f"Missing one or more of the following required parameters: {required_parameters}")
                            return
                            
                        persona_config = {
                            "id": f"persona:{args.persona_name}",
                            "name": args.persona_name,
                            "description": parsed_params['description'],
                            "author": naptha.hub.user_id,
                            "url": parsed_params['url'],
                            "version": parsed_params['version'],
                        }
                        await create_persona(naptha, persona_config)
                else:
                    print("Invalid command.")
            elif args.command == "run":
                if hasattr(args, 'parameters') and args.parameters is not None:
                    try:
                        parsed_params = json.loads(args.parameters)
                    except json.JSONDecodeError:
                        params = shlex.split(args.parameters)
                        parsed_params = {}
                        for param in params:
                            key, value = param.split('=')
                            parsed_params[key] = value
                else:
                    parsed_params = None
                
                # parse worker nodes
                if hasattr(args, 'worker_nodes') and args.worker_nodes is not None:
                    worker_node_urls = args.worker_nodes.split(',')
                else:
                    worker_node_urls = "http://localhost:7001"

                # parse environment nodes 
                if hasattr(args, 'environment_nodes') and args.environment_nodes is not None:
                    environment_node_urls = args.environment_nodes.split(',')
                else:
                    environment_node_urls = ["postgresql://naptha:naptha@localhost:3002/naptha"]

                # parse personas urls
                if hasattr(args, 'personas_urls') and args.personas_urls is not None:
                    personas_urls = args.personas_urls.split(',')
                else:
                    personas_urls = None
                print(f"Personas URLs: {personas_urls}")
                await run(naptha, args.agent, user_id, parsed_params, worker_node_urls, environment_node_urls, args.file, personas_urls)
            elif args.command == "read_storage":
                await read_storage(naptha, args.agent_run_id, args.output_dir, args.ipfs)
            elif args.command == "write_storage":
                await write_storage(naptha, args.storage_input, args.ipfs, args.publish_to_ipns, args.update_ipns_name)
            elif args.command == "publish":
                await naptha.publish_agents()
        else:
            parser.print_help()

def cli():
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())