function neighbourhoodHighlight(params) {
    console.log("in nieghborhoodhighlight");
    console.log(params);
    highlightActive = false;
    allNodes = nodes.get({ returnType: "Object" }); //    Call by value
    allEdges = edges.get({ returnType: "Object" });
    console.log(allEdges);
    console.log(allNodes);
    // originalNodes = JSON.parse(JSON.stringify(allNodes));
    // if something is selected:
    if (params.nodes.length > 0) {
        highlightActive = true;
        var i, j;
        var selectedNode = params.nodes[0];
        var degrees = 2;
        nodeList = network.getConnectedNodes(selectedNode);
        console.log(nodeList);

        //Getting all edges for the selected node
        edgeList = network.nodesHandler.getConnectedEdges.apply(network, params.nodes);
        console.log(edgeList);

        //Getting all edges per node
        var processedEdgeList = new Object();
        // For all edges of Base Node- Create an associative array
        edgeList.forEach(function(edgeId, index) {
            processedEdgeList[edgeId] = network.getConnectedNodes(edgeId); // Call by value
        });

        //Processing Edges
        //Changing Inward edges color to green and outward to red
        for (var edgeId in allEdges) {
            // nodeColors[nodeId] = allNodes[nodeId].color;
            //All nodes associated with the selected node - value 1 and varied color
            if (edgeList.includes(edgeId)) {
                //Outward Nodes to red
                console.log("I am in edge logic");
                console.log(processedEdgeList);

                if (processedEdgeList[edgeId][0] == selectedNode) {
                    console.log("I am in outward edge");
                    allEdges[edgeId].value = 1;
                    allEdges[edgeId].color = "rgba(227, 36, 27, 1)";
                } else {
                    allEdges[edgeId].value = 1;
                    allEdges[edgeId].color = "rgba(116, 191, 75, 1)";
                }
            } else { // Non-Highlighted Nodes
                //Change weight to 0.5
                allEdges[edgeId].value = 0.5;
                allEdges[edgeId].color = "rgba(189, 195, 199, 1)";
            }
        }

        console.log(processedEdgeList);
        // allEdges[]
        // mark all nodes as hard to read.
        for (var nodeId in allNodes) {
            // nodeColors[nodeId] = allNodes[nodeId].color;
            nodeColors[nodeId] = "rgba(13, 39, 77, 1)";
            allNodes[nodeId].color = "rgba(0, 188, 235, 1)";
            if (allNodes[nodeId].hiddenLabel === undefined) {
                allNodes[nodeId].hiddenLabel = allNodes[nodeId].label;
                allNodes[nodeId].label = undefined;
            }
        }

        var connectedNodes = network.getConnectedNodes(selectedNode);
        var allConnectedNodes = [];

        // get the second degree nodes
        for (i = 1; i < degrees; i++) {
            for (j = 0; j < connectedNodes.length; j++) {
                allConnectedNodes = allConnectedNodes.concat(
                    network.getConnectedNodes(connectedNodes[j])
                );
            }
        }

        // all second degree nodes get a different color and their label back
        for (i = 0; i < allConnectedNodes.length; i++) {
            // allNodes[allConnectedNodes[i]].color = "pink";
            // allNodes[allConnectedNodes[i]].color = "rgba(251, 171, 44, 1)";
            if (allNodes[allConnectedNodes[i]].hiddenLabel !== undefined) {
                allNodes[allConnectedNodes[i]].label =
                    allNodes[allConnectedNodes[i]].hiddenLabel;
                allNodes[allConnectedNodes[i]].hiddenLabel = undefined;
            }
        }

        // all first degree nodes get their own color and their label back
        //Permanent color
        for (i = 0; i < connectedNodes.length; i++) {
            // allNodes[connectedNodes[i]].color = undefined;
            // allNodes[connectedNodes[i]].color = nodeColors[connectedNodes[i]];
            allNodes[connectedNodes[i]].color = "rgba(251, 171, 44, 1)";
            if (allNodes[connectedNodes[i]].hiddenLabel !== undefined) {
                allNodes[connectedNodes[i]].label =
                    allNodes[connectedNodes[i]].hiddenLabel;
                allNodes[connectedNodes[i]].hiddenLabel = undefined;
            }
        }

        // the main node gets its own color and its label back.
        // allNodes[selectedNode].color = "rgba(116, 191, 75, 1)";
        allNodes[selectedNode].color = nodeColors[selectedNode];
        if (allNodes[selectedNode].hiddenLabel !== undefined) {
            allNodes[selectedNode].label = allNodes[selectedNode].hiddenLabel;
            allNodes[selectedNode].hiddenLabel = undefined;
        }
    } else
    if (highlightActive === true) {
        console.log("highlightActive was true");
        // reset all nodes
        for (var nodeId in allNodes) {
            // allNodes[nodeId].color = "purple";
            allNodes[nodeId].color = nodeColors[nodeId];
            // delete allNodes[nodeId].color;
            if (allNodes[nodeId].hiddenLabel !== undefined) {
                allNodes[nodeId].label = allNodes[nodeId].hiddenLabel;
                allNodes[nodeId].hiddenLabel = undefined;
            }
        }
        // reset all edges
        for (var edgeId in allEdges) {
            // Non-Highlighted Nodes
            //Change weight to 0.5
            allEdges[edgeId].value = 1;
            allEdges[edgeId].color = "rgba(189, 195, 199, 1)";
        }
        highlightActive = false;


    }

    // transform the object into an array for nodes
    var updateArray = [];
    if (params.nodes.length > 0) {
        for (nodeId in allNodes) {
            if (allNodes.hasOwnProperty(nodeId)) {
                // console.log(allNodes[nodeId]);
                updateArray.push(allNodes[nodeId]);
            }
        }
        nodes.update(updateArray);
    } else {
        console.log("Nothing was selected");
        for (nodeId in allNodes) {
            if (allNodes.hasOwnProperty(nodeId)) {
                // console.log(allNodes[nodeId]);
                // allNodes[nodeId].color = {};
                updateArray.push(allNodes[nodeId]);
            }
        }
        nodes.update(updateArray);
    }

    // transform the object into an array for edges
    var updateArray = [];
    if (params.nodes.length > 0) {
        for (edgeId in allEdges) {
            if (allEdges.hasOwnProperty(edgeId)) {
                // console.log(allNodes[nodeId]);
                updateArray.push(allEdges[edgeId]);
            }
        }
        edges.update(updateArray);
    } else {
        console.log("Nothing was selected");
        for (edgeId in allEdges) {
            if (allEdges.hasOwnProperty(edgeId)) {
                // console.log(allNodes[nodeId]);
                // allNodes[nodeId].color = {};
                updateArray.push(allEdges[edgeId]);
            }
        }
        edges.update(updateArray);
    }
}

function selectNode(node) {
    network.selectNodes([node]);
    neighbourhoodHighlight({ nodes: [node] });
    return node;
}