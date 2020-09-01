.PHONY: check
check: all test

.PHONY: rebuild
rebuild: clean all

# Call the repo root Makefile to build the ctags db
.PHONY: ctags
.NOTPARALLEL: ctags
ctags:
	@ $(MAKE) -C $(MLOS_ROOT) ctags
	@ echo "make ctags target finished."
