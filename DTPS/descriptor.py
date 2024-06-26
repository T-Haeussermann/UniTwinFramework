import inspect
import json
import importlib
import os



def generate_function_json(func):
    parameters = inspect.signature(func).parameters
    json_data = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": f"Function {func.__name__}",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }

    for param_name, param in parameters.items():

        if param_name != "self":
            param_type = str(param.annotation)
            # print(param_type)
            if param_type == "<class 'inspect._empty'>":
                param_type = "string"  # default type if no annotation is provided

            json_data["function"]["parameters"]["properties"][param_name] = {
                "type": param_type,
                "description": f"The {param_name} parameter."
            }

            if param.default != inspect._empty:
                json_data["function"]["parameters"]["properties"][param_name]["default"] = param.default

    required_params = [param_name for param_name, param in parameters.items() if param.default == inspect._empty and param_name != "self"]
    json_data["function"]["parameters"]["required"] = required_params

    return json_data

finalDS = {}
for classFile in os.listdir("Modules"):
    if "__" not in classFile and "Event" not in classFile:
        try:
            item = classFile.replace(".py", "")
            globals()[item] = getattr(importlib.import_module("Modules." + item), item)
            for fct in globals()[item].__dict__:
                if "__" not in fct and "configure_router" not in fct and "_abc_impl" not in fct:
                    if type(getattr(globals()[item], fct)) != property:
                        fct_ds = generate_function_json(getattr(globals()[item], fct))
                        if item not in finalDS:
                            finalDS[item] = {}
                        finalDS[item][fct] = fct_ds
        except Exception as e:
            print(f"skipped {item}")
            print(e)

for item in finalDS:
    with open(f"Descriptions/{item}.json", "w") as file:
        json.dump(finalDS[item], file, indent=2)

