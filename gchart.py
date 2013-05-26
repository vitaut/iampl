# Google Chart wrapper for iampl.

from IPython.core.display import Javascript

def GeoChart(keys, data, **kwargs):
    table = "{},\n".format(keys)
    for i in data:
        table += "['{}', {}],\n".format(i, data[i])
    options = ""
    for arg, value in kwargs.iteritems():
        if isinstance(value, bool):
            value = 'true' if value else 'false'
        elif isinstance(value, dict):
            items = ""
            for k, v in value.iteritems():
                items += "{}: {},".format(k, v)
            value = "{{{}}}".format(items)
        options += "{}:{},\n".format(arg, value)
    return Javascript("""
        container.show();
        function draw() {{
          var chart = new google.visualization.GeoChart(element[0]);
          chart.draw(google.visualization.arrayToDataTable([{}]), {{{}}});
        }}
        google.load('visualization', '1.0', {{'callback': draw, 'packages':['geochart']}});
        """.format(table, options), lib="https://www.google.com/jsapi")