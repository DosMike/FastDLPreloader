#!/usr/bin/env python3
import sys, os, pathlib, argparse, time, re, bz2, time
import urllib.request


crawl_files = 0
crawl_dirs = 0
crawl_start = 0

option_replace = False


def create_index(url):
    global crawl_files, crawl_dirs

    path = url[url.index('/', url.index('.')):]
    print(f'-- Scanning {path}')
    with urllib.request.urlopen(url) as f:
        content = f.read().decode('utf-8')

    links = [x.group(1) for x in re.finditer(r'<a href="([^"]*)">', content)]
    links = [x for x in links if not x.startswith(('/','?'))] # remove meta links
    files = [url+x for x in links if not x.endswith('/')] # dirs end in /
    nfiles = len(files)
    ndirs = len(links)-nfiles
    crawl_files += nfiles
    crawl_dirs += ndirs
    print(f'   Files: {crawl_files} (+{nfiles})  Dirs: {crawl_dirs} (+{ndirs})')
    for sub in [x for x in links if x.endswith('/')]:
        crawl_dirs -= 1
        files = files + create_index(url + sub)
    return files


def fetch_and_unpack(url, path, progress):
    global option_replace, crawl_start

    path.parent.mkdir(parents=True, exist_ok=True)
    target = path.parent / path.name.removesuffix('.bz2') if path.name.endswith('.bz2') else path
    tmpfile = path.parent / (target.name+'.tmp')

    if target.exists() and not option_replace:
        return

    print(f'-- Downloading {progress[0]}/{progress[1]}: {target}')
    
    if path.name.endswith('.bz2'):
        decomp = bz2.BZ2Decompressor()
        with urllib.request.urlopen(url) as f, open(tmpfile, 'wb') as t:
            while chunk := f.read(16*1024):
                t.write(decomp.decompress(chunk))
    else:
        with urllib.request.urlopen(url) as f, open(tmpfile, 'wb') as t:
            while chunk := f.read(16*1024):
                t.write(chunk)

    if target.exists():
        target.unlink() # windows does not replace
    tmpfile.rename(target)
        


def download(target):
    global crawl_start
    baseurl = 'https://lazypurple.com/tf/fastdl/tf/' #<-- should end in slash
    files = create_index(baseurl)
    count = 0
    crawl_start = time.time()
    for next in files:
        if not next.startswith(baseurl):
            continue
        relative = next[len(baseurl):]
        dest = target / relative
        count += 1
        fetch_and_unpack(next, dest, (count, len(files)))


def main(args):
    if not args:
        if sys.stdin and sys.stdin.isatty():
            args = ['--help']
        else:
            import tkinter as tk  # install python3-tk
            tk.messagebox.showinfo('LP FastDL Preloader', 'This is a console application')
            return

    parser = argparse.ArgumentParser(prog='lp_fastdl_preloader', description='Download all of fastdl into a directory. Place this script into your tf2 installation directory, next to tf_win64.exe / tf_linux64. The default download directory of the game is "tf/download", but you can also download to a mod directory with "tf/custom/lazypurple".', epilog='Bottom text')
    parser.add_argument('-r', '--replace', action='store_true', help='Ignore existing files and replace them. If not set, existing files are ignored')
    parser.add_argument('-t', '--directory', type=pathlib.Path, required=True)
    arguments = parser.parse_args(args)
    if not (arguments.directory.is_dir() or (not arguments.directory.exists() and arguments.directory.parent.is_dir())):
        print('Target directory is not a directory or parent directory does not exist')
        sys.exit(1)
    
    global option_replace
    option_replace = arguments.replace
    arguments.directory.mkdir(exist_ok=True)
    download(arguments.directory.resolve())


if __name__ == '__main__':
    main(sys.argv[1:])
