# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: console\main.py
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

import os
import sys
import inquirer
from art import text2art
from colorama import Fore
from inquirer.themes import GreenPassion
from rich import box
from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from loader import config

sys.path.append(os.path.realpath('.'))

class Console:
    MODULES = ('Register', 'Farm', 'Multiple farm', 'Re-verify accounts', 'Export statistics', 'Exit')
    MODULES_DATA = {'Register': 'register', 'Farm': 'farm', 'Exit': 'exit', 'Export statistics': 'export_statistics', 'Multiple farm': 'multiple_farm', 'Re-verify accounts': 'verify'}

    def __init__(self):
        self.rich_console = RichConsole()

    def show_dev_info(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        title = text2art('JamBit', font='small')
        styled_title = Text(title, style='bold cyan')
        version = Text('VERSION: 1.6', style='blue')
        dev_panel = Panel(Text.assemble(styled_title, '\n', version), border_style='yellow', expand=False, title='[bold green]Welcome[/bold green]', subtitle='[italic]Powered by Jammer[/italic]')
        self.rich_console.print(dev_panel)
        print()

    @staticmethod
    def prompt(data: list):
        answers = inquirer.prompt(data, theme=GreenPassion())
        return answers

    def get_module(self):
        questions = [inquirer.List('module', message=Fore.LIGHTBLACK_EX + 'Select the module', choices=self.MODULES)]
        answers = self.prompt(questions)
        if not answers:
            return 'Exit'
        return answers.get('module')

    def display_info(self):
        table = Table(title='Gradient Configuration', box=box.ROUNDED)
        table.add_column('Parameter', style='cyan')
        table.add_column('Value', style='magenta')
        table.add_row('Accounts to register', str(len(config.accounts_to_register)))
        table.add_row('Accounts to farm', str(len(config.accounts_to_farm)))
        table.add_row('Accounts to re-verify', str(len(config.accounts_to_verify)))
        table.add_row('Threads', str(config.threads))
        table.add_row('Delay before start', f'{config.delay_before_start.min} - {config.delay_before_start.max} sec')
        panel = Panel(table, expand=False, border_style='green', title='[bold yellow]System Information[/bold yellow]', subtitle='[italic]Use arrow keys to navigate[/italic]')
        self.rich_console.print(panel)

    def build(self) -> None:
        self.show_dev_info()
        self.display_info()
        module = self.get_module()
        config.module = self.MODULES_DATA[module]