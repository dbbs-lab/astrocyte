import os

def get_minimum_glia_version():
    # TODO: Use pip to find the installed glia version.
    return "0.0.1-a5"

def get_constants():
    return {
        "glia_version": get_minimum_glia_version()
    }

def parse_template(name, locals={}):
    file = open(os.path.join(os.path.dirname(__file__), "templates", name + ".txt"), "r")
    template_string = file.read()
    for local, value in locals.items():
        template_string = template_string.replace("{{"+local+"}}", str(value))
    for const, value in get_constants().items():
        template_string = template_string.replace("{|"+const+"|}", str(value))

    return template_string

def create_template(name, target, locals={}):
    content = parse_template(name, locals)
    template = open(os.path.join(target, name), "w")
    template.write(content)
    template.close()
