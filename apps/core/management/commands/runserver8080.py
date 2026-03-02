from django.core.management.commands.runserver import Command as RunserverCommand


class Command(RunserverCommand):
    help = 'Starts a development server on port 8080'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.set_defaults(addrport='127.0.0.1:8080')
