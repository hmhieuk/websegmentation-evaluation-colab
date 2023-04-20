from lxml import html

# Parse the HTML document
doc = html.parse("000000/dom.html")
# get xpath of all elements
elems = doc.xpath("//*")

for elem in elems:
    xpath = doc.getpath(elem)
    
    # Split the XPath string into separate tags
    tags = xpath.split("/")[1:]

    # Replace each tag with its uppercased name and index (if present)
    for i, tag in enumerate(tags):
        if "[" in tag:
            # The tag already has an index, so just uppercase the tag name
            tag_name, index = tag.split("[")
            tags[i] = tag_name.upper() + "[" + index
        else:
            # The tag doesn't have an index, so add a default "[1]"
            tags[i] = tag.upper() + "[1]"

    # Join the tags back together into a single XPath string
    result = "/" + "/".join(tags)

    print(result)
