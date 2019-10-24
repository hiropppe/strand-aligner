import click
import requests
import sys

from html_similarity import style_similarity, structural_similarity, similarity


@click.command()
@click.option("--lang1", "-l1", default="English", type=click.Choice(["English", "Japanese"]), required=True)
@click.option("--lang2", "-l2", default="Japanese", type=click.Choice(["English", "Japanese"]), required=True)
@click.option("--url1", "-u1", required=False)
@click.option("--url2", "-u2", required=False)
@click.option("--file1", "-f1", required=False)
@click.option("--file2", "-f2", required=False)
@click.option("--enc1", "-e1", default="utf8")
@click.option("--enc2", "-e2", default="utf8")
def main(lang1, lang2, url1, url2, file1, file2, enc1, enc2):
    if url1 and url2:
        html1 = requests.get(url1).content.decode(
            enc1, "replace").replace("\n", " ").replace("\t", " ")
        html2 = requests.get(url2).content.decode(
            enc2, "replace").replace("\n", " ").replace("\t", " ")
    else:
        html1 = open(file1).read().replace("\n", " ").replace("\t", " ")
        html2 = open(file2).read().replace("\n", " ").replace("\t", " ")
        url1 = "http://test.com/{:s}".format(lang1)
        url2 = "http://test.com/{:s}".format(lang2)

    print("style_similarity={:f} structural_similarity={:f} similarity={:f}".format(
        style_similarity(html1, html2), structural_similarity(html1, html2), similarity(html1, html2)), file=sys.stderr)

    print("\t".join(["dummy_key", lang1, url1, html1, lang2, url2, html2]))


if __name__ == "__main__":
    main()
