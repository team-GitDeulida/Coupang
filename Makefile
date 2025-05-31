.PHONY: all update

all: update

update:
	git add .
	git commit -m "update"
	git push origin main
