.PHONY: all check clean

objects = $(wildcard *.in)
outputs := $(objects:.in=.txt)

all: $(outputs)

%.txt: %.in
	pip-compile -v --output-file $@ $<

server.txt: base.txt

local.txt: base.txt

test.txt: local.txt server.txt

check:
	@which pip-compile > /dev/null

clean: check
	- rm *.txt
