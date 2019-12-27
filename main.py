import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.listview import ListItemButton
from urllib.request import Request, urlopen
import requests
from kivy.uix.label import Label
import cfscrape
import threading
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import time
from selenium.common.exceptions import NoSuchElementException  
import regex
from datetime import date
import os
import requests



#loaded in data is saved here
open_file = {}
file_type = 'na'
last_command = ''

#sequence object that is used to store each sequence inside the file seperately for easier processing
class sequence(object):
  # init method
  def __init__(self, sequence_header, sequence):
    
    self.sequence_name = sequence_header
    self.sequence = sequence

#object holding all data from the read in file
class loaded_file(object):
  # init method
  def __init__(self, file_name, sequence_list):
    
    self.file_name = file_name
    if '.aln' in file_name:
        self.type = 'aln'
    elif '.fa' in file_name:
        self.type = 'fasta'
    elif ".fasta" in file_name:
        self.type = 'fasta'
    else:
        self.type = 'invalid'
    self.sequence_list = sequence_list


#logs errors and informs user of error
def log_error(message):
    today = date.today()
    if len(open_file) > 0:
        view = view()
    else:
        view = 'empty'
    output = 'Message: ' + message + '\n'
    output = output + 'Command: ' + last_command + '\n'
    output = output + 'Date: ' + str(today) + '\n' + view + '\n\n\n' + '-_-_-_-_-_-_-_-_-_-_-_-_-_-' + '\n'

    with open("log.txt", "a") as log_file:
        log_file.write(output)
    return message

#checks if an element exists on a webpage
def check_exists_by_xpath(browser, xpath):
    try:
        browser.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True



#reads in a file line by line
def get_lines(file_name):
    try:
        line_list = list()
        with open(file_name) as f:
            for line in f:
                line_list.append(line) #.rsplit()
        return line_list
    except:
        return log_error('Issue in get_lines which likely means the file can not be found. Check that your file name is correctly spelled in the input and that the file is in the same folder as this program\'s .exe ')




def load_file(file_name):
    #reads in by lines and saves to an array
    lines_in_file = get_lines(file_name)
    if 'Issue in ' in lines_in_file:
        return lines_in_file
    #identify as clustal or fasta file
    try:
        if 'CLUSTAL' in lines_in_file[0]:
            #converts from clustal to fasta file
            file_type = '.aln'
            url = 'https://www.ebi.ac.uk/Tools/sfc/emboss_seqret/'
            opts = Options()
            opts.headless = True
            download_dir = str(os.getcwd()) + '\\chromedriver.exe'
            path_to_chromedriver = download_dir
            browser = webdriver.Chrome(executable_path = path_to_chromedriver, chrome_options=opts)
            browser.get(url)
            file = ''
            for x in lines_in_file:
                file = file + str(x)

            browser.execute_script("""
            var file = arguments[0];
            document.getElementsByName('sequence')[0].value=file;
            """, file)
            
            browser.find_element_by_xpath('//*[@id="outputformat"]/option[11]').click()
            browser.execute_script("arguments[0].click();", browser.find_element_by_xpath('//*[@id="jd_submitButtonPanel"]/input'));

            while check_exists_by_xpath(browser, '//*[@id="outputContent"]') == False:
                time.sleep(.05)
            lines_in_file = browser.find_element_by_id('outputContent').text.splitlines()



        elif '>' in lines_in_file[0]:
            file_type = '.fa'

        #Converts the fasta formatted array into a fasta format compliant array
        smallerlist = [l.split(',') for l in ','.join(lines_in_file).split('>')]
        smallerlist.remove(smallerlist[0])
        for x in smallerlist:
            x[0] = ('>') + x[0] 
            if x != smallerlist[-1]:
                x.remove(x[-1])

        sequence_list = list()

        #saves object to temp db seperating the header and the sequence and saving them to the loaded file object
        for x in smallerlist:
            header = x.pop(0).strip('\n')
            current_sequence = "".join(x).strip('\n')

            sequence_list.append(sequence(header, current_sequence))

        
        open_file['loaded'] = loaded_file(file_name, sequence_list)
        
        #returns  success indicator
        return ('Successfully read in : ', file_name)
    except:
        return log_error('Error in Load_file. Check your input files formatting and if you input a .aln file check that your internet is working.')




def view():
    #checks that the file is loaded in
    #returns the currently loaded file to view
    try:
        if open_file != '':
            output = ''
            output = output + 'Loaded File Name:\n' + open_file['loaded'].file_name + '\n\nOf File type:\n' + open_file['loaded'].type + '\n\n'
            for x in open_file['loaded'].sequence_list:
                output = output + 'Header:\n' + x.sequence_name + '\n'
                output = output + 'Sequence:\n' + x.sequence + '\n\n'
            return str(output)
        else:
            return 'File not loaded'
    except:
        return log_error('Issue in view, check that a file is loaded in')

    


def search(query, mismatch_amount, reverse_flag):
    try:
        output = ''
        sequences = open_file['loaded'].sequence_list
        #Searches the sequences and outputs the matches
        for x in sequences:
            output = output + '\nSearching sequence: \n' + str(x.sequence) + '\n\n'
            m=regex.findall("(" + str(query) + "){e<=" + str(mismatch_amount) + "}", str(x.sequence.replace('-', '')))
            if len(m) > 0:
                output = output + 'Found match of: \n'
                for x in m:
                    output = output + x + '\n'
            else:
                output = output + 'None found'

        #Searches the sequences in reverse and outputs the matches
        if reverse_flag == True:
            rev_query = query[::-1]
            for x in sequences:
                output = output + ' Reverse Searching sequence: \n' + str(x.sequence) + '\n\n'
                m=regex.findall("(" + str(rev_query) + "){e<=" + str(mismatch_amount) + "}", str(x))
                if len(m) > 0:
                    output = output + 'Found match of: \n'
                    for x in m:
                        output = output + x + '\n'
                else:
                    output = output + 'None found'

        return output
    except:
        return log_error('Issue in Search, check that your query is directly after search (ex: search query) and that if you used mismatch what followed it is a valid number. Also check that a valid file is loaded in.')


def rename(prefix, clear_flag):
    try:
        sequences = open_file['loaded'].sequence_list
        output = 'Added prefix to:'
        #loops through all sequences adding the prefix to each sequences header
        for x in sequences:
            x.sequence_name = '>' + str(prefix) + x.sequence_name.replace('>', "")

            if clear_flag == True:
                x.sequence_name = x.sequence_name.split(' ')[0]
            output = output + '\n' + x.sequence_name

        return output
    except:
        return log_error('Issue in rename, check that a file is loaded in.')


def save(file_name):
    #saves currently loaded in file(post commands being done to it) as the provided filename. If .aln it saves as clustal and if .fa it saves as fasta if neither defaults to fasta 
    try:
        output = ''
        sequences = open_file['loaded'].sequence_list
        #formats the saved data into fasta format
        for s in sequences:
            if s != sequences[-1]:
                output = output + s.sequence_name + '\n' + s.sequence + '\n'
            else:
                output = output + s.sequence_name + '\n' + s.sequence
        #sends the fasta to seqret for it to return a clustal formatted sequence set
        if '.aln' in file_name:
            url = 'https://www.ebi.ac.uk/Tools/sfc/emboss_seqret/'
            opts = Options()
            opts.headless = True
            download_dir = str(os.getcwd()) + '\\chromedriver.exe'
            path_to_chromedriver = download_dir
            browser = webdriver.Chrome(executable_path = path_to_chromedriver, chrome_options=opts)
            browser.get(url)
            

            browser.execute_script("""
            var output = arguments[0];
            document.getElementsByName('sequence')[0].value=output;
            """, output)
            
            browser.find_element_by_xpath('//*[@id="outputformat"]/option[32]').click()
            browser.execute_script("arguments[0].click();", browser.find_element_by_xpath('//*[@id="jd_submitButtonPanel"]/input'));

            while check_exists_by_xpath(browser, '//*[@id="outputContent"]') == False:
                time.sleep(.05)
            output = browser.find_element_by_id('outputContent').text
        
        f = open(file_name, "a")
        f.write(str(output))
        f.close()
    except:
        return log_error('Issue in Save, check that a file is loaded in and if it is a .aln file you have internet')



def trim(front, back):
    try:
        sequences = open_file['loaded'].sequence_list
        #removes the requested amount from the front and back and then returns the view
        for x in sequences:
            if front != False:
                x.sequence = x.sequence[(int(front)):]
            if back != False:
                x.sequence = x.sequence[:(-int(back))]

        return view()
    except:
        return log_error('Issue in Trim, check that a file is loaded in and that a number directly follows front/back depending on which you used or both.')


def boxshade():
    try:
        output = ''
        sequences = open_file['loaded'].sequence_list
        #formats the sequences to fasta format
        for s in sequences:
            if s != sequences[-1]:
                output = output + s.sequence_name + '\n' + s.sequence + '\n'
            else:
                output = output + s.sequence_name + '\n' + s.sequence
        #converts to inital file type and runs it through the labs process.

        #sends the fasta to be boxshaded
        url = 'https://embnet.vital-it.ch/software/BOX_form.html'
        opts = Options()
        opts.headless = True
        download_dir = str(os.getcwd()) + '\\chromedriver.exe'
        path_to_chromedriver = download_dir
        browser = webdriver.Chrome(executable_path = path_to_chromedriver, chrome_options=opts)
        browser.get(url)
        

        browser.execute_script("""
        var output = arguments[0];
        document.getElementsByName('seq')[0].value=output;
        """, output)
        
        browser.find_element_by_xpath('//*[@id="sib_body"]/center/table/tbody/tr/td/form/table/tbody/tr[1]/td[2]/h3[1]/select/option[8]').click()
        browser.find_element_by_xpath('//*[@id="sib_body"]/center/table/tbody/tr/td/form/table/tbody/tr[5]/td[2]/h3/select/option[3]').click()
        browser.execute_script("arguments[0].click();", browser.find_element_by_xpath('//*[@id="sib_body"]/center/table/tbody/tr/td/form/table/tbody/tr[7]/td/center/h3/input[1]'));

        while check_exists_by_xpath(browser, '//*[@id="sib_body"]/a[1]') == False:
            time.sleep(.05)
        #downloads the resulting boxshade to a file named "filename.rtf". The file name is created based on the input file name
        link = (str(browser.find_element_by_xpath('//*[@id="sib_body"]/a[1]').get_attribute('href')))
        r = requests.get(link, allow_redirects=True)
        open(open_file['loaded'].file_name.split('.')[0] + '.rtf', 'wb').write(r.content)
        return (open_file['loaded'].file_name.split('.')[0] + '.rtf downloaded')
    except:
        return log_error('Issue in boxshade, check that a file is loaded in, you have internet connection, and that your sequences are valid.')
    #output = browser.find_element_by_id('outputContent').text
    #puts all results in the same file

def degap():
    try:
        sequences = open_file['loaded'].sequence_list
        #formats the sequences to fasta format
        for s in sequences:
            s.sequence = s.sequence.replace('-', '')

        open_file['loaded'].sequence_list = sequences
        return view()
    except:
        return log_error('Degap has failed, check that a file is loaded in and that the sequences are valid.')

def help_u():
    try:
        output = 'Commands: \n'
        #help
        output = output + 'help  : Displays this message with commands as well as there uses and examples of them \n Ex: help\n\n'
        #Load CN.fa
        output = output + 'load  : Loads the file in for use by this program. file must be located in the same folder as this program. accepts .aln , .fa, and .fasta files \n Ex: load test.fasta\n\n'
        #Save file.fasta
        output = output + 'save  : Saves the file currently in the program to a file. can save as a fasta or aln file. \n Ex: save backup.fasta\n\n'
        #Trim -front 10 -back 2
        output = output + 'trim  : Trims from the front and back of the sequences in the loaded in file. you can enter in a front value back value or both \n Ex: trim -front 10 -back 2\n Ex: trim -front 10\n Ex: trim -back 2\n\n'
        #Rename Cel_ -clear
        output = output + 'rename  : Renames the headers by adding to the front of the seqeuences. If clear is set to true it clears everything in the header minus the first word (words defined as character sets split by spaces) \n Ex: rename id_\n Ex: rename id_ -clear\n\n'
        #Search AER -reverse -mismatch 2
        output = output + 'search  : Searches for the included query. Has a reverse flag which also searches in reverse for matches. Has mismatch that allows for a certain number of substitutions insertions or deletions. \n Ex: search AER \n Ex: Ex: search AER -mismatch 2\n Ex: search AER -mismatch 2 -reverse\n\n'
        #boxshade
        output = output + 'boxshade  : Takes the prepared fasta file (might need to be aligned) that has been loaded in and downloads a boxshade in the same folder as this program generated from the loaded file . \n Ex: boxshade\n\n'
        #view
        output = output + 'view  : Shows the currently loaded file seperating the headers and sequences in order to make them easy to look over. \n Ex: view\n\n'
        return output
    except:
        return log_error('Help has failed which should be impossible so congratulations.')


# home page of application that holds the users list of lightnovel series. The user can add to the list, delete from it or go to an item added on the list from here.
class Main_Page(Screen):
    #prepares the objects on the front end to be interactable
    command_input_text = ObjectProperty()
    output_text = ObjectProperty()
    
    #Used to set the ouput text
    def output(self, text):
        output = str(text)
        self.output_text.text = output
    #calls run in a thread so that it doesnt freeze the program while longer processes are running
    def run_in_thread(self):
        threading.Thread(target=self.run).start()


    def run(self):
        try:
            #splits up the input command and calls the appropriate function based on the flag after seperating the command into multiple arguments
            result = ''
            command = str(self.command_input_text.text)
            last_command = command
            if command != "":
                self.command_input_text.text = ""
                if  'load' in command.lower():
                    result = load_file(command.split(' ')[1])

                elif 'view' in command.lower():
                    result = view()
                elif 'search' in command.lower():
                    #Search AER -reverse -mismatch 2
                    commands = command.split(' ')
                    query = commands[1]
                    mismatch_amount = 0
                    reverse_flag = False
                    for x in commands:
                        if '-mismatch' in x:
                            mismatch_amount = (commands[commands.index(x)+1])
                    if '-reverse' in x:
                        reverse_flag = True
                    result = search(query, mismatch_amount, reverse_flag)

                elif 'rename' in command.lower():
                    commands = command.split(' ')
                    if '-clear' in command:
                        clear_flag = True
                    else:
                        clear_flag = False
                    result = rename(commands[1], clear_flag)
                #Trim front 10 back 2 - show_all
                elif 'trim' in command.lower():
                    commands = command.split(' ')
                    front = False
                    back = False
                    for x in commands:
                        if '-front' in x:
                            front = (commands[commands.index(x)+1])
                        if '-back' in x:
                            back = (commands[commands.index(x)+1])
                    result = trim(front, back)
                elif 'save' in command.lower():
                    commands = command.split(' ')
                    save(commands[1])
                elif 'help' in command.lower():
                    result =  help_u()
                
                elif 'degap' in command.lower():
                    result = degap()

                elif 'boxshade' in command.lower():
                    result = boxshade()
                else:
                    result = 'invalid command'

                self.ids['scroll'].scroll_y = 1
                self.output(result)
        except:
            self.output(log_error('There is an issue processing that command, please check that it is valid'))






# runs the program using a screen manager that holds the screen and makes adding multiple screens if needed possible
class String_Manipulator(App):
    def build(self):
        screen_manager = ScreenManager()
        screen_manager.add_widget(Main_Page(name="screen_one"))
        return screen_manager


if __name__ == '__main__':
    smApp = String_Manipulator()
    smApp.run()
