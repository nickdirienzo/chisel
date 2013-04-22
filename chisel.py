#!/usr/bin/python

# Chisel
# David Zhou
# 
# Requires:
# jinja2
# markdown

# Modified by Nick DiRienzo

import datetime
import sys, re, time, os, codecs
import jinja2, markdown

#Settings
SOURCE = "./posts/" #end with slash
DESTINATION = "./export/" #end with slash
HOME_SHOW = 15 #numer of entries to show on homepage
TEMPLATE_PATH = "./templates/default/"
TEMPLATE_OPTIONS = {}
TEMPLATES = {
    'home': "home.html",
    'detail': "detail.html",
    'archive': "archive.html",
}
TIME_FORMAT = "%B %d, %Y"
ENTRY_TIME_FORMAT = "%m/%d/%Y"
#FORMAT should be a callable that takes in text
#and returns formatted text
FORMAT = lambda text: markdown.markdown(text, ['footnotes',]) 
#########

STEPS = []
COMMANDS = dict()

def step(func):
    def wrapper(*args, **kwargs):
        print "Starting " + func.__name__ + "...",
        func(*args, **kwargs)
        print "Done."
    STEPS.append(wrapper)
    return wrapper

def command(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
    COMMANDS[func.__name__] = wrapper
    return wrapper

def get_tree(source):
    files = []
    for root, ds, fs in os.walk(source):
        for name in fs:
            if name[0] == ".": continue
            path = os.path.join(root, name)
            ext = os.path.splitext(path)[1]
            if ext == '.md' or ext == '.markdown':
                with open(path, 'rU') as f:
                    title = f.readline()
                    date = time.strptime(f.readline().strip(), ENTRY_TIME_FORMAT)
                    year, month, day = date[:3]
                    files.append({
                        'title': title,
                        'epoch': time.mktime(date),
                        'content': FORMAT(''.join(f.readlines()[1:]).decode('UTF-8')),
                        'url': os.path.join(str(year), '%.2d' % month, os.path.splitext(name)[0]),
                        'pretty_date': time.strftime(TIME_FORMAT, date),
                        'date': date,
                        'year': year,
                        'month': month,
                        'day': day,
                        'filename': name,
                    })
    return files

def compare_entries(x, y):
    result = cmp(-x['epoch'], -y['epoch'])
    if result == 0:
        return -cmp(x['filename'], y['filename'])
    return result

def write_file(url, data):
    path = DESTINATION + url
    dirs = os.path.dirname(path)
    if not os.path.isdir(dirs):
        os.makedirs(dirs)
    file = open(path, "w")
    file.write(data.encode('UTF-8'))
    file.close()

@step
def generate_homepage(f, e):
    """Generate homepage"""
    template = e.get_template(TEMPLATES['home'])
    write_file("index.html", template.render(entries=f[:HOME_SHOW]))

@step
def master_archive(f, e):
    """Generate master archive list of all entries"""
    template = e.get_template(TEMPLATES['archive'])
    write_file("archives.html", template.render(entries=f))

@step
def detail_pages(f, e):
    """Generate detail pages of individual posts"""
    template = e.get_template(TEMPLATES['detail'])
    for file in f:
        write_file(os.path.join(file['url'], 'index.html'), template.render(entry=file))

@command
def serve():
    import BaseHTTPServer, SimpleHTTPServer
    os.chdir(DESTINATION) # assume that we are in the top dir
    address = ('127.0.0.1', 8080)
    httpd = BaseHTTPServer.HTTPServer(address, SimpleHTTPServer.SimpleHTTPRequestHandler)
    print 'Listening on port:', str(address[1])
    httpd.serve_forever()

@command
def new():
    import subprocess
    title = raw_input("Enter post title: ")
    filename = ''.join(['-'.join(title.split()), '.md'])
    path = os.path.join(SOURCE, filename)
    if os.path.exists(path):
        print 'Post %s already exists. Exiting.' % title
    else:
        with open(path, 'w') as f:
            f.write(title)
            f.write('\r\n')
            f.write(datetime.date.today().strftime(ENTRY_TIME_FORMAT))
            f.write('\r\n')
            f.write('\r\n')
            f.write('\r\n')
        subprocess.call(['vim', path])

def main():
    if len(sys.argv) == 2:
        if sys.argv[1] in COMMANDS:
            COMMANDS[sys.argv[1]]()
        else:
            print '''usage: python chisel.py [<command>]

Possible commands:
    serve       Run a local server to preview your generated content
    new         Create a new post and bring up vim to edit it
'''

    elif len(sys.argv) == 1:
        print "Chiseling..."
        print "\tReading files...",
        files = sorted(get_tree(SOURCE), cmp=compare_entries)
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH), **TEMPLATE_OPTIONS)
        print "Done."
        print "\tRunning steps..."
        for step in STEPS:
            print "\t\t",
            step(files, env)
        print "\tDone."
        print "Done."
        

if __name__ == "__main__":
    sys.exit(main())
