#!/usr/bin/python

# Chisel
# David Zhou
# 
# Requires:
# jinja2
# markdown

# Modified by Nick DiRienzo

import calendar
import datetime
import sys, re, time, os, codecs
import jinja2, markdown
import slugify

#Settings
SOURCE = "./posts/" #end with slash
DESTINATION = "./export/" #end with slash
HOME_SHOW = 0 #numer of entries to show on homepage
TEMPLATE_PATH = "./templates/nick.dirienzo.co/"
TEMPLATE_OPTIONS = {}
TEMPLATES = {
    'home': "home.html",
    'detail': "detail.html",
    'archive': "archive.html",
    'about': 'about.html',
    'projects': 'projects.html'
}
STATIC_PATH = './static/'
TIME_FORMAT = "%b %d, %Y"
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
            slug, ext = os.path.splitext(path)
            slug = ''.join([slug.split('/')[-1], '.html'])
            if ext == '.md':
                with open(path, 'rU') as f:
                    title = f.readline()
                    date = time.strptime(f.readline().strip(), ENTRY_TIME_FORMAT)
                    year, month, day = date[:3]
                    files.append({
                        'title': title,
                        'epoch': time.mktime(date),
                        'content': FORMAT(''.join(f.readlines()[1:]).decode('UTF-8')),
                        'url': os.path.join(str(year), '%.2d' % month, slug),
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
def gen_about(f, e):
    template = e.get_template(TEMPLATES['about'])
    write_file(os.path.join('about', 'index.html'), template.render(page='about'))

@step
def gen_projects(f, e):
    template = e.get_template(TEMPLATES['projects'])
    write_file(os.path.join('projects', 'index.html'), template.render(page='projects'))

@step
def generate_homepage(f, e):
    """Generate homepage"""
    template = e.get_template(TEMPLATES['home'])
    write_file("index.html", template.render(entries=f, page='home'))

# Uncomment the below line to bring the archive back. We generate it on the home page now.
#@step
def master_archive(f, e):
    """Generate master archive list of all entries"""
    template = e.get_template(TEMPLATES['archive'])
    write_file(os.path.join('archive', 'index.html'), template.render(entries=f, page='archive'))

@step
def detail_pages(f, e):
    """Generate detail pages of individual posts"""
    template = e.get_template(TEMPLATES['detail'])
    for file in f:
        write_file(file['url'], template.render(entry=file))

@step
def dir_archive(files, env):
    """ For every year and year-month directory, generate an archive page (just so the URL still works) """
    template = env.get_template(TEMPLATES['archive'])
    for f in files:
        e_path = os.path.join(DESTINATION, str(f['year']).zfill(2), 'index.html')
        w_path = os.path.join(str(f['year']).zfill(2), 'index.html')
        if not os.path.isfile(e_path):
            write_file(w_path, template.render(entries=filter(lambda x: x if x['year'] == f['year'] else None, files), page='archive'))

        e_path = os.path.join(DESTINATION, str(f['year']).zfill(2), str(f['month']).zfill(2), 'index.html')
        w_path = os.path.join(str(f['year']).zfill(2), str(f['month']).zfill(2), 'index.html')
        if not os.path.isfile(e_path):
            write_file(w_path, template.render(entries=filter(lambda x: x if x['month'] == f['month'] and x['year'] == f['year'] else None, files), page='archive'))


@step
def copy_static(f, e):
    import distutils.dir_util
    distutils.dir_util.copy_tree(STATIC_PATH, os.path.join(DESTINATION, 'static'))

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
    filename = ''.join([slugify.slugify(title), '.md'])
    path = os.path.join(SOURCE, filename)
    today = datetime.datetime.now()
    if os.path.exists(path):
        print 'Post %s already exists. Exiting.' % title
    else:
        with open(path, 'w') as f:
            f.write(title)
            f.write('\r\n')
            f.write(today.strftime(ENTRY_TIME_FORMAT))
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
