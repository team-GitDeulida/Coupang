.PHONY: all update

all: update

update:
	git pull origin main
	git add .
	git commit -m "update"
	git push origin main
