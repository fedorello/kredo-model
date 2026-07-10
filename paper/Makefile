all: main.pdf main-ru.pdf

main.pdf: main.tex
	tectonic main.tex

# Russian version needs a Unicode engine (fontspec/Cyrillic); Tectonic uses XeTeX.
main-ru.pdf: main-ru.tex
	tectonic main-ru.tex

clean:
	rm -f main.pdf main-ru.pdf *.aux *.log *.out

.PHONY: all clean
