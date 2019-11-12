compile: compile-maxent compile-strand

install: install-maxent install-strand

compile-maxent:
	cd maxent && make && python3 setup.py build_ext -i

compile-strand:
	cd strand && make && python3 setup.py build_ext -i

install-maxent:
	cd maxent && python3 setup.py install

install-strand:
	cd strand && python3 setup.py develop

.PHONY: clean
clean:
	cd maxent && make clean
	cd strand && make clean
