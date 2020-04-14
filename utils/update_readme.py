import datetime
import os
import sys
from configparser import ConfigParser
from shutil import copyfile
from datetime import datetime, timedelta

READ_ME_PATH = '..\\readme.md'
DAILY_LOG_PATH = '..\\daily_log.md'
BACKUP_READ_ME_PATH = '..\\readme.md_{0}_{1}.bak'
STREAK_SEARCH_VAL = 'Current Daily Streak'
CURRENT_STREAK_SEARCH_DATE_VAL = 'Current Streak Dates'
LAST_STREAK_SEARCH_DATE_VAL = 'Last Streak Dates'
PROJECT_END_SEARCH_STR = '<!--- {0} end --->'
DATE_FORMAT_STR="%m/%d/%Y"

'''
A quick and dirty script to update readme and dailylog
'''
class ReadMeUpdater():
    def __init__(self, config_file_path='config.ini'):
        try:
            if not os.path.exists(config_file_path):
                raise FileNotFoundError(config_file_path)

            if not os.path.exists(READ_ME_PATH):
                raise FileNotFoundError(READ_ME_PATH)

            self.config = ConfigParser()
            self.config.read(config_file_path)
            self.lines = None
            with open(READ_ME_PATH, 'r') as file_handler:
                self.lines = file_handler.readlines()
            
            day_number = datetime.today().day
            min_number = datetime.today().minute
            copyfile(READ_ME_PATH, BACKUP_READ_ME_PATH.format(day_number, min_number))
            
            self.search_terms = []
            self.search_index = {}

            self.__build_search_terms()
            self.__build_search_index()
        except Exception as e:
            print('Something went while reading configurations', str(e))
            sys.exit()

    def __build_search_index(self):
        for i, elem in enumerate(self.lines):
            for term in self.search_terms:
                if term in elem:
                    self.search_index[term] = i

    def __build_search_terms(self):
        update_streak = self.config['StreakSection'].getboolean('UpdateStreak')
        streak_broken = self.config['StreakSection'].getboolean('StreakBroken')
        if update_streak:
            self.search_terms.append(STREAK_SEARCH_VAL)
            self.search_terms.append(CURRENT_STREAK_SEARCH_DATE_VAL)
            if streak_broken:
                self.search_terms.append(LAST_STREAK_SEARCH_DATE_VAL)
        update_project = self.config['ProjectUpdateSection'].getboolean('UpdateProject')
        if update_project:
            project_section = self.config.get('ProjectUpdateSection', 'Section')
            self.search_terms.append(PROJECT_END_SEARCH_STR.format(project_section))

    def __increment_streak_line(self, streak_line, streak_date_line, streak_broken):
        lst = streak_line.split('|')
        if not streak_broken:
            seq_no = int(lst[2]) + 1
            streak_dates_str = streak_date_line.split('|')
            date_list = streak_dates_str[2].split('-')
            date_obj0 = datetime.strptime(date_list[0].strip(), DATE_FORMAT_STR)
            date_obj1 = datetime.strptime(date_list[1].strip(), DATE_FORMAT_STR)
            delta = (date_obj1 - date_obj0).days + 1
            assert delta == seq_no, F"Delta {delta}, seq:{seq_no}, date1: {date_obj0}, date2: {date_obj1}"
        else:
            seq_no = 1
        lst[2] = F' {seq_no} '
        return '|'.join(lst)
    
    def __increment_streak_date_line(self, line, streak_broken):
        lst = line.split('|')
        date_list = lst[2].split('-')
        todays_date = datetime.now().strftime(DATE_FORMAT_STR)
        if not streak_broken:
            date_obj = datetime.strptime(date_list[1].strip(), DATE_FORMAT_STR)
            date_obj += timedelta(days=1)  
            new_date = date_obj.strftime(DATE_FORMAT_STR)
            assert todays_date == new_date, F'Todays date: {todays_date}, new date: {new_date}'
            date_list[1] = F' {new_date} '
        else:
            date_list[0] = F' {todays_date} '
            date_list[1] = F' {todays_date} '
        lst[2] = '-'.join(date_list)
        return '|'.join(lst)

    def __reset_last_streak_date_line(self, last_streak, cur_streak):
        lst = last_streak.split('|')
        cur = cur_streak.split('|')
        cur_date_list = cur[2].split('-')
        lst_date_list = lst[2].split('-')
        lst_date_list[0] = cur_date_list[0]
        lst_date_list[1] = F' {(datetime.now() - timedelta(2)).strftime(DATE_FORMAT_STR)} '
        lst[2] = '-'.join(lst_date_list)
        return '|'.join(lst)

    def _get_next_proj_seq_no(self, section):
        index = self.search_index[PROJECT_END_SEARCH_STR.format(section)]
        prev_proj_line = self.lines[index-1]
        seq_no_elements = prev_proj_line.split('|')[1].split('.')
        seq_no = int(seq_no_elements[0]) + 1
        return seq_no

    def __build_project_string(self):
        update_project = self.config['ProjectUpdateSection'].getboolean('UpdateProject')
        if not update_project:
            return
        proj_section = self.config.get('ProjectUpdateSection', 'Section')
        index = self.search_index[PROJECT_END_SEARCH_STR.format(proj_section)]
        proj_name = self.config.get('ProjectUpdateSection', 'Project')
        proj_desc = self.config.get('ProjectUpdateSection', 'Description')
        proj_notebook = self.config.get('ProjectUpdateSection', 'Notebook')
        proj_notes = self.config.get('ProjectUpdateSection', 'Notes')
        seq_no = self._get_next_proj_seq_no(proj_section)        
        line = F"|{seq_no}.| {proj_name} | {proj_desc} | {proj_notebook} | {proj_notes} |\n"
        return (index, line)

    def update_streak_stats(self):
        update_streak = self.config['StreakSection'].getboolean('UpdateStreak')
        streak_broken = self.config['StreakSection'].getboolean('StreakBroken')
        if not update_streak:
            return
        cur_streak_date_line = self.lines[self.search_index[CURRENT_STREAK_SEARCH_DATE_VAL]]
        cur_streak_line = self.lines[self.search_index[STREAK_SEARCH_VAL]]
        new_last_streak_date_line = ""
        if streak_broken:
            last_streak_date_line = self.lines[self.search_index[LAST_STREAK_SEARCH_DATE_VAL]]
            new_last_streak_date_line = self.__reset_last_streak_date_line(last_streak_date_line, cur_streak_date_line)
            self.lines[self.search_index[LAST_STREAK_SEARCH_DATE_VAL]] = new_last_streak_date_line
        new_cur_streak_date_line = self.__increment_streak_date_line(cur_streak_date_line, streak_broken)
        new_cur_streak_line = self.__increment_streak_line(cur_streak_line, new_cur_streak_date_line, streak_broken)
        self.lines[self.search_index[CURRENT_STREAK_SEARCH_DATE_VAL]] = new_cur_streak_date_line
        self.lines[self.search_index[STREAK_SEARCH_VAL]] = new_cur_streak_line
    
    def add_new_project(self):
        update_project = self.config['ProjectUpdateSection'].getboolean('UpdateProject')
        if not update_project:
            return
        index, new_proj_line = self.__build_project_string()
        self.lines.insert(index, new_proj_line)
        

    def print_search_index(self):
        for k,v in self.search_index.items():
            print (k, ":", v)

    def save_readme(self, path=READ_ME_PATH):
        with open(path, 'w') as file_handler:
            file_handler.writelines(self.lines)

    def update_daily_log(self, path=DAILY_LOG_PATH):
        update_daily_log = self.config['DailyLogSection'].getboolean('UpdateDailyLog')
        if not update_daily_log:
            return
        notes = self.config.get('DailyLogSection', 'Notes')
        date = datetime.now().strftime('%d %B %Y')
        new_line = F'| {date} | {notes} |\n'
        with open(path, 'a') as file_handler:
            file_handler.write(new_line)
            


readMeUpdater = ReadMeUpdater()
readMeUpdater.print_search_index()
readMeUpdater.update_streak_stats()
readMeUpdater.add_new_project()
readMeUpdater.save_readme('readme2.md')
readMeUpdater.update_daily_log()





