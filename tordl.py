#!/usr/bin/env python
# -*- coding: utf-8 -*-
import curses, locale, sys, itertools, os
from operator import itemgetter, attrgetter
from urlparse import urlparse
import pycurl
import downloader
#~ curses.start_color()
#~ curses.cbreak()
#~ curses.raw()
class pane:
	def __init__(self, title, height, width, y, x, boxed):
		self.title = title
		self.pads = {}
		self.curline = 0
		self.height = height
		try:
			self.win = curses.newwin(self.height, width, y, x)
		except curses.error:
			print 'Can\'t create Pane window'
			sys.exit(-1)
		self.win.leaveok(1)
		self.win.keypad(1)
		if boxed: self.win.box()
		if (self.title == 'Proxies'):
			attr = curses.A_STANDOUT
		else:
			attr = curses.A_NORMAL
		self.chfocus(attr)
	def addpad(self, name, width):
		self.pads[name] = curses.newpad((self.height -  1), width)
	def fillpad(self, padname, values, width):
		for line, value in enumerate(values):
			if line == self.curline:
				self.pads[padname].addnstr(line+1, 1, value, width, curses.A_STANDOUT)
			else:
				self.pads[padname].addnstr(line+1, 1, value, width)
	def refreshpad(self, padname, y, x, width):
		self.pads[padname].noutrefresh(1,1, y,x, (y + self.height - 2), (x +width))
	def chfocus(self, attr):
		self.win.addstr(0, 2, self.title, attr)
		self.win.noutrefresh()
class ui_main:
	def __init__(self):
		locale.setlocale(locale.LC_ALL, '')
		stdscr = curses.initscr()
		(self.scr_height, self.scr_width) = stdscr.getmaxyx()
		curses.halfdelay(18)
		curses.curs_set(0)
		curses.noecho()
		self.quit = False
		self.proxy_height = 11
		self.proxy_width = 30
		#~ self.download_height = 11
		self.jobs = []
		self.proxy_pane = pane('Proxies', self.proxy_height, self.proxy_width, 0,0, True)
		self.download_pane = pane('Downloads', self.scr_height - self.proxy_height - 2, self.scr_width, self.proxy_height, 0, True)
		#~ self.download_pane = pane('Downloads', 11, self.scr_width - self.width1, 0,30, True)
		self.input_pane = pane('', 2, self.scr_width, self.scr_height - 2, 0, False)
		self.act_pane = self.proxy_pane
		self.panes = self.gen_panes()
		self.exitnodes = downloader.getnodes()[0:9]
		if len(self.exitnodes) == 0:
			self.exitnodes = ['uranus', 'technowargod', 'blutmagie', 'UBIT2', 'desync', 'gpfTOR3', '100MbitdedicatedRLY', 'bach', 'dragonking']
		#~ self.exitnodes = ['uranus', 'technowargod', 'blutmagie', 'UBIT2', 'desync', 'gpfTOR3', '100MbitdedicatedRLY', 'bach', 'dragonking']
		self.ports = ['-', '-', '-', '-', '-', '-', '-', '-', '-']
	def gen_panes(self):
		panes = [self.download_pane, self.proxy_pane]
		for pane in itertools.cycle(panes):
			yield pane
	def initpanes(self):
		self.proxy_pane.addpad('num', 3)
		self.proxy_pane.addpad('names', 21)
		self.proxy_pane.addpad('ports', 5)
		self.download_pane.addpad('percent', 4)
		self.download_pane.addpad('downloaded', 12)
		self.download_pane.addpad('size', 12)
		self.download_pane.addpad('filename', self.scr_width - 44)
		self.download_pane.addpad('proxy', 2)
		self.download_pane.addpad('speed', 4)
		self.download_pane.addpad('time_left', 9)
	def draw_all(self):
		self.draw_proxies()
		self.draw_downloads()
		curses.doupdate()
	def draw_proxies(self):
		self.proxy_pane.pads['ports'].clear()
		self.proxy_pane.pads['names'].clear()
		self.proxy_pane.pads['num'].clear()
		self.proxy_pane.fillpad('num', [str(x) for x in xrange(1,10)], 3)
		self.proxy_pane.refreshpad('num', 1,1, 3)
		self.proxy_pane.fillpad('names', self.exitnodes, 21)
		self.proxy_pane.refreshpad('names', 1,4, 21)
		self.proxy_pane.fillpad('ports', self.ports, 5)
		self.proxy_pane.refreshpad('ports', 1, 25, 5)
	def draw_downloads(self):
		self.download_pane.pads['percent'].clear()
		self.download_pane.pads['downloaded'].clear()
		self.download_pane.pads['size'].clear()
		self.download_pane.pads['proxy'].clear()
		self.download_pane.pads['speed'].clear()
		self.download_pane.pads['time_left'].clear()
		self.download_pane.pads['filename'].clear()
		if len(self.jobs):
			if (self.download_pane.curline + 1) > len(self.jobs):
				self.download_pane.curline = len(self.jobs) - 1
			percent = [str(x.percent) for x in self.jobs]
			self.download_pane.fillpad('percent', percent, 4)
			downloaded = [str(x.downloaded) for x in self.jobs]
			self.download_pane.fillpad('downloaded', downloaded, 12)
			size = [str(x.size) for x in self.jobs]
			self.download_pane.fillpad('size', size, 12)
			proxy = [str(x.proxy) for x in self.jobs]
			self.download_pane.fillpad('proxy', proxy, 2)
			speed = [str(x.speed) for x in self.jobs]
			self.download_pane.fillpad('speed', speed, 4)
			time_left = [str(x.time_left) for x in self.jobs]
			self.download_pane.fillpad('time_left', time_left, 9)
			filename = [str(x.filename) for x in self.jobs]
			self.download_pane.fillpad('filename', filename, self.scr_width - 44)
		self.download_pane.refreshpad('percent', self.proxy_height + 1, 1, 4)
		self.download_pane.refreshpad('downloaded', self.proxy_height + 1, 5, 12)
		self.download_pane.refreshpad('size', self.proxy_height + 1, 17, 12)
		self.download_pane.refreshpad('proxy', self.proxy_height + 1, 29, 2)
		self.download_pane.refreshpad('speed', self.proxy_height + 1, 31, 4)
		self.download_pane.refreshpad('time_left', self.proxy_height + 1, 35, 9)
		self.download_pane.refreshpad('filename', self.proxy_height + 1, 44, self.scr_width - 44)
	def run(self):
		keyaction = { curses.KEY_UP: self.up, curses.KEY_DOWN: self.down, ord('\t'):  self.toggle_active_pane, ord(' '): self.toggleproxy,
			ord('a'): self.add, curses.KEY_DC: self.delete }
		input = self.act_pane.win.getch()
		if input == ord('q'):
			curses.endwin()
			self.quit = True
			return 0
		try:
			keyaction.get(input)()
		except TypeError:
			pass
		self.draw_all()
	def delete(self):
		if self.act_pane == self.download_pane:
			try: 
				self.jobs[self.download_pane.curline].cancel = True
				self.jobs[self.download_pane.curline].finished.wait()
				self.jobs[self.download_pane.curline].c.close()
				self.jobs[self.download_pane.curline].file.close()
				self.jobs.pop(self.download_pane.curline)
			except IndexError: pass
	def add(self):
		curses.curs_set(1)
		curses.echo()
		while True:
			self.input_pane.win.addnstr(0, 1, 'URL:', 4)
			url = self.input_pane.win.getstr(0, 5, (2 * self.scr_width) - 7)
			self.input_pane.win.clear()
			self.input_pane.win.refresh()
			o = urlparse(url)
			if o.scheme in ['http', 'https'] and o.netloc:
				Curl = downloader.curl(url, 12)
				break
		while True:
			self.input_pane.win.addnstr(0, 1, 'Proxy:', 6)
			proxy = self.input_pane.win.getkey(0, 7)
			try: 
				proxy = int(proxy)
				break
			except:
				self.input_pane.win.clear()
				self.input_pane.win.refresh()
		self.input_pane.win.addnstr(0, 1, 'Resume (y/N):', 13)
		resume = self.input_pane.win.getkey(0, 14)
		if proxy:
			Curl.setproxy( str(9074 + proxy - 1) )
			Curl.proxy = str(proxy)
		if resume in ('y', 'Y'):
			try:
				Curl.resume_from = os.path.getsize('./' + Curl.filename)
				Curl.file = open('./' + Curl.filename, 'ab')
			except OSError:
				Curl.file = open('./' + Curl.filename, 'wb')
		else:
			Curl.file = open('./' + Curl.filename, 'wb')
		#~ Curl.file = open('./' + Curl.filename, 'wb')
		Curl.start()
		self.jobs.append(Curl)
		self.input_pane.win.clear()
		self.input_pane.win.refresh()
		curses.noecho()
		curses.halfdelay(18)
		curses.curs_set(0)
	def up(self):
		if self.act_pane.curline > 0:
			self.act_pane.curline -= 1
	def down(self):
		if self.act_pane == self.proxy_pane:
			limit = 9
		elif self.act_pane == self.download_pane:
			limit = len(self.jobs)
		if self.act_pane.curline == (limit - 1):
			self.act_pane.curline = 0
		else:
			self.act_pane.curline += 1
	def toggle_active_pane(self):
		self.act_pane.chfocus(curses.A_NORMAL)
		self.act_pane = self.panes.next()
		self.act_pane.chfocus(curses.A_STANDOUT)
	def toggleproxy(self):
		if self.act_pane == self.proxy_pane:
			portnum = str(9074 + self.proxy_pane.curline)
			if self.ports[self.proxy_pane.curline] == '-':
				downloader.start_tor(self.exitnodes[self.proxy_pane.curline], portnum)
				self.ports[self.proxy_pane.curline] = portnum
			else:
				downloader.stop_tor(portnum)
				self.ports[self.proxy_pane.curline] = '-'
if __name__ == "__main__":
	interface = ui_main()
	interface.initpanes()
	while True:
		interface.run()
		if interface.quit:
			#~ print len(interface.jobs)
			exit()
