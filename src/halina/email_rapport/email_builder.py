import logging
from jinja2 import Environment, FileSystemLoader
import os

logger = logging.getLogger(__name__.rsplit('.')[-1])


def generate_email_content(template_name, context):
    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    template = env.get_template(template_name)
    return template.render(context)
