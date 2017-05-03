import sys
import os
import copy
import collections
from compiler.ast import flatten
import json

def fixPath(output_file, path):
    with open(output_file, 'r') as file :
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace('**FULLPATH**', path)

    # Write the file out again
    with open(output_file, 'w') as file:
        file.write(filedata)

"""
Writes one of the two static parts to output.
Both are statically included at the end of this file.
:param me: this file
:param output_file: output html file
:param start: string determining beginning of the part
:param end: string determining end of the part
:param mode: append or write
"""
def write_part(part, output_file, mode):
    with open(output_file, mode) as file:
        file.write(part)

"""
Creates collection from given side
:param side: given string containing side of a rule
:return: collection
"""
def create_collection(side):
	return collections.Counter(flatten(map(lambda (k, v): [k]*int(v), side.iteritems())))

"""
Removes pairs of same agents from left and right side, i.e. creates a reaction.
:param From: left-hand-side
:param To: right-hand-side
:return: sides with reduced agents
"""
def create_reaction(From, To):
    From = create_collection(From)
    To = create_collection(To)

    left = From - To
    right = To - From

    left = map(lambda (a,b): b.__str__() + " " + a, left.items())
    right = map(lambda (a,b): b.__str__() + " " + a, right.items())

    return " + ".join(left), " + ".join(right)

"""
Writes new vertex to output file
:param vertex_id: internal ID of the vertex
:param ID: external ID of the vertex (hash)
:param label: explicit information about content of the vertex
:param output_file: output html file
"""
def write_entity(vertex_id, ID, label, output_file):
    output = open(output_file, 'a')
    output.write("\t{id: " + vertex_id.__str__() + ", label: '" + vertex_id.__str__() + "', title: 'ID " + ID.__str__() + "', text: '" + label.__str__() + "'},\n")
    output.close()

"""
Writes new edge to output file
:param edge_id: ID of the edge
:param left_index: internal ID of out-coming vertex
:param right_index: internal ID of in-coming vertex
:param From: left-hand-side of reaction
:param To: right-hand-side of the reaction
:param output_file: output html file
"""
def write_reaction(edge_id, left_index, right_index, From, To, output_file):
    output = open(output_file, 'a')
    output.write("\t{id: " + edge_id.__str__() + ", from: " + left_index.__str__() + ", to: " + right_index.__str__() +
                 ", arrows:'to', text: '" + From.__str__() + " => " + To.__str__() + "'},\n")
    output.close()

def write_size(screenWidth, screenHeight, output_file):
    with open(output_file, "a") as file:
        file.write("            width: " + str(screenWidth-50) + "px;\n")
        file.write("            height: " + str(screenHeight-100) + "px;")

def createHTMLGraph(state_space_file, output_file, path, screenWidth, screenHeight):

    write_part(firstpart_1, output_file, "w")
    write_size(screenWidth, screenHeight, output_file)
    write_part(firstpart_2, output_file, "a")
    write_part(str(screenWidth - 50), output_file, "a")
    write_part(firstpart_3, output_file, "a")

    with open(state_space_file, 'r') as f:
    	data = json.load(f)

    IDs = dict()
    vertex_id = 0
    for key, value in data['nodes'].iteritems():
    	vertex_id += 1
    	label = ""
    	for k, v in value.iteritems():
    		label += v + " " + k + "<br>"
    	write_entity(vertex_id, key, label, output_file)
    	IDs[key] = vertex_id

    output = open(output_file, 'a')
    output.write("\t]);\n\n\t// create an array with edges\n\tvar edges = new vis.DataSet([\n")
    output.close()

    for edge_id, value in data['edges'].iteritems():
    	From, To = create_reaction(data['nodes'][value['from']], data['nodes'][value['to']])
    	write_reaction(edge_id, IDs[value['from']], IDs[value['to']], From, To, output_file)
    		
    write_part(secondpart_1, output_file, "a")
    write_part(str(screenWidth - 50), output_file, "a")
    write_part(secondpart_2, output_file, "a")

    fixPath(output_file, path)

    return output_file

def createSVGGraph(state_space_file, output_file, path):
    return output_file

def add_nodes(graph, nodes):
    for n in nodes:
        if isinstance(n, tuple):
            graph.node(n[0], **n[1])
        else:
            graph.node(n)
    return graph

def add_edges(graph, edges):
    for e in edges:
        if isinstance(e[0], tuple):
            graph.edge(*e[0], **e[1])
        else:
            graph.edge(*e)
    return graph

def newGraph(state_space_file, path, type, screenWidth, screenHeight):
    if type:
        return createHTMLGraph(state_space_file, "graph.html", path, screenWidth, screenHeight)
    else:
        return createSVGGraph(state_space_file, "graph.svg", path)

firstpart_1 = \
'''<!doctype html>
<html>
<head>
    <title>Network | Interaction events</title>

    <script type="text/javascript" src="**FULLPATH**/.vis/vis.js"></script>
    <link href="**FULLPATH**/.vis/vis.css" rel="stylesheet" type="text/css"/>

    <style type="text/css">
       #mynetwork {
'''

firstpart_2 = '''
            border: 1px solid lightgray;
        }
	    #rectangle {
		    text-align: center;
		    font-weight: bold;
	    }
}
    </style>
</head>
<body>

<div id="mynetwork"></div>
<div id="rectangle"style="width:'''

firstpart_3 = '''px;height:100%;border:1px solid #000;"> </div>

<script type="text/javascript">
    // create an array with nodes
        var nodes = new vis.DataSet([
'''

secondpart_1 = '''
	]);

    // create a network
    var container = document.getElementById('mynetwork');
    var data = {
        nodes: nodes,
        edges: edges
    };
    var options = {
		layout: {improvedLayout: true},
        physics: {
            enabled: true,
            barnesHut: {
                gravitationalConstant: -25000,
                centralGravity: 0.5,
                springConstant: 0.5,
                springLength: 200,
                damping: 0.15
            },
            maxVelocity: 50,
            minVelocity: 7.5,
            solver: 'barnesHut',
            timestep: 0.5,
            stabilization: {
                        enabled:true,
                        iterations:5000,
                    },
        },
		nodes: {
            size: 15,
            font: {
                size: 20
            },
            borderWidth: 2,
			borderWidthSelected: 4,
            color:{highlight:{border: '#B20F0F', background: 'red'}}
        },
        edges: {
            width: 4,
			selectionWidth: function (width) {return width*2.5;},
            color:{color:'#2B7CE9', hover:'#2B7CE9', highlight: 'red'}
        },
		interaction: {
          navigationButtons: true,
          keyboard: true,
		  hover: true,
		  tooltipDelay: 500,
          multiselect: true
        }
	};
    var network = new vis.Network(container, data, options);
	var stabil = true;

    network.on("click", function (params) {
        params.event = "[original event]";
		var tmp = " ";


		for (var i = 1; i <= nodes.length; i++) {
        	if (nodes.get(i).id == params.nodes) {
				tmp = nodes.get(i).text;
			};
    	};

		if(params.nodes.length === 0 && params.edges.length > 0) {
			for (var i = 1; i <= edges.length; i++) {
				if (edges.get(i).id == params.edges) {
					tmp = edges.get(i).text;
				};
			};
		};

		document.getElementById('rectangle').innerHTML = '<div style="width:'''

secondpart_2 = '''px;height:100%;text-align:center;border:0px solid #000;">' + tmp + '</div>';
    });

	network.on("stabilized", function (params) {
	if(stabil) {
		network.fit();
		stabil = false;
	};
	});

	network.on("doubleClick", function (params) {
        params.event = "[original event]";
		network.focus(params.nodes);
	});

</script>

<script src="../../googleAnalytics.js"></script>
</body>
</html>
'''