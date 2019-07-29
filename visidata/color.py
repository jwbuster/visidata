import curses
import functools
import copy

from visidata import options

__all__ = ['ColorAttr', 'colors']


class ColorAttr:
    def __init__(self, attr=0, precedence=-1):
        self.attributes = attr & ~curses.A_COLOR
        self.color = attr & curses.A_COLOR
        self.precedence = precedence

    def __str__(self):
        a = self.attr
        ret = set()
        for k in dir(curses):
            v = getattr(curses, k)
            if v == 0:
                pass
            elif k.startswith('A_'):
                if self.attributes & v == v:
                    ret.add(k)
            elif k.startswith('COLOR_'):
                if self.color == v:
                    ret.add(k)
        return (' '.join(k for k in ret) or str(self.color)) + ' %0X' % self.attr

    @property
    def attr(self):
        'the composed curses attr'
        return self.color | self.attributes

    def update_attr(self, newattr, newprec=None):
        if isinstance(newattr, int):
            newattr = ColorAttr(newattr)
        ret = copy.copy(self)
        if newprec is None:
            newprec = newattr.precedence
        ret.attributes |= newattr.attributes
        if not ret.color or newprec > ret.precedence:
            if newattr.color:
                ret.color = newattr.color
            ret.precedence = newprec
        return ret


class ColorMaker:
    def __init__(self):
        self.attrs = {}
        self.color_attrs = {}
        self.colorcache = {}

    def setup(self):
        if options.use_default_colors:
            curses.use_default_colors()
            default_bg = -1
        else:
            default_bg = curses.COLOR_BLACK

        self.color_attrs['black'] = curses.color_pair(0)

        for c in range(0, options.force_256_colors and 256 or curses.COLORS):
            try:
                curses.init_pair(c+1, c, default_bg)
                self.color_attrs[str(c)] = curses.color_pair(c+1)
            except curses.error as e:
                pass # curses.init_pair gives a curses error on Windows

        for c in 'red green yellow blue magenta cyan white'.split():
            colornum = getattr(curses, 'COLOR_' + c.upper())
            self.color_attrs[c] = curses.color_pair(colornum+1)

        for a in 'normal blink bold dim reverse standout underline'.split():
            self.attrs[a] = getattr(curses, 'A_' + a.upper())

    def keys(self):
        return list(self.attrs.keys()) + list(self.color_attrs.keys())

    def __getitem__(self, colornamestr):
        return self._colornames_to_cattr(colornamestr).attr

    def __getattr__(self, optname):
        'colors.color_foo returns colors[options.color_foo]'
        return self.get_color(optname).attr

    @functools.lru_cache()  # cleared in vd.clear_caches()
    def resolve_colors(self, colorstack):
        'Returns the ColorAttr for the colorstack, a list of color option names sorted highest-precedence color first.'
        cattr = ColorAttr()
        for coloropt in colorstack:
            c = self.get_color(coloropt)
            cattr = cattr.update_attr(c)
        return cattr

    def _colornames_to_cattr(self, colornamestr, precedence=0):
        cattr = ColorAttr(0, precedence)
        for colorname in colornamestr.split(' '):
            if colorname in self.color_attrs:
                if not cattr.color:
                    cattr.color = self.color_attrs[colorname.lower()]
            elif colorname in self.attrs:
                cattr.attributes |= self.attrs[colorname.lower()]
        return cattr

    def get_color(self, optname, precedence=0):
        'colors.color_foo returns colors[options.color_foo]'
        r = self.colorcache.get(optname, None)
        if r is None:
            coloropt = options._get(optname)
            colornamestr = coloropt.value if coloropt else optname
            r = self.colorcache[optname] = self._colornames_to_cattr(colornamestr, precedence)
        return r

colors = ColorMaker()
