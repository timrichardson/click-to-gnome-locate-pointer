PREFIX ?= $(HOME)/.local
BINDIR ?= $(PREFIX)/bin
DESTDIR ?=

PROGRAM := click-to-gnome-locate-pointer
SCRIPT := click-to-gnome-locate-pointer.py

.PHONY: install uninstall

install:
	install -d "$(DESTDIR)$(BINDIR)"
	install -m 755 "$(SCRIPT)" "$(DESTDIR)$(BINDIR)/$(PROGRAM)"

uninstall:
	rm -f "$(DESTDIR)$(BINDIR)/$(PROGRAM)"
