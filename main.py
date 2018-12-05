import py_org


def read_file(path):
    f = open(path, "rb")
    contents = f.read().decode('utf8')
    f.close()
    return contents


def parse_json(path):
    contents = read_file(path)
    q.add_parse(contents)


def write_output(path, contents):
    f = open(path, "wb")
    f.write(contents.encode('utf8'))
    f.close()


# Create and populate an empty Org document. (Create)
q = py_org.Org()
parse_json("input1.json")
parse_json("input2.json")
write_output("journal.org", str(q))

# Create and populate an Org document from an existing one. (Append)
q = py_org.Org()
q.parse(read_file("journal.org"))
parse_json("input3.json")
write_output("journal2.org", str(q))