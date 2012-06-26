RM  := rm -rf

sources := $(wildcard *.c)
objects := $(subst .c,.o,$(sources))    

test_sources := $(wildcard test/*.c)
test_objects := $(subst .c,.o,$(test_sources))    


CFLAGS += -g -Wall
CPPFLAGS += -I.

all: 

.PHONY: all libadt testlist
all: libadt testlist

libadt: $(objects)
	$(CC) $(CFLAGS) $(CPPFLAGS) -dynamiclib -o libadt.so $^

#	$(AR) rc lib/libkluge.a $^

testlist: $(test_sources) libadt.so
	$(CC) $(CFLAGS) $(CPPFLAGS) -o test/testlist $^


objects: $(sources) $(test_sources)
	$(CC) $(CFLAGS) 

.PHONY: clean 
clean: 
	$(RM) $(objects) $(test_objects) *~ libadt.so test/testlist test/testlist.dSYM test/*~ 

