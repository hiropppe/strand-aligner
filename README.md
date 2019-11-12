A little modified [STRANDAligner](https://github.com/jrs026/STRANDAligner) including python3 support

# STRAND Aligner
An implementation of the HTML alignment algorithm of STRAND:

P. Resnik and N. A Smith. The web as a parallel corpus. Computational
Linguistics, 29(3):349-380, 2003.

This also contains an implementation of the Gale and Church sentence alignment
algorithm:

W. A. Gale and K. W. Church. A program for aligning sentences in
bilingual corpora. Computational Linguistics, 19:75-102, March 1993.

## Setup
```
make
make install
```

## Usage
```
strand-align --help
Usage: strand-align [OPTIONS]

Options:
  -i, --input-file TEXT         Location of the uncompressed mined webpages
  -n, --num-entries TEXT        Maximum number of entries to examine, set to 0
                                for no limit
  -o, --out-prefix TEXT         Parallel data will be output to this location
  -sa, --sentence-aligner [GC]  Sentence alignment implementation
  -ib64, --input-base64         See input html as base64 encoded
  -ob64, --output-base64        Output base64 encoded text
  -ah, --align-href             align href attribute value or not
  --help                        Show this message and exit.
```
