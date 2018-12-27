# Skvoretz-AGM
Synthetic Attribute Graph Model (AGM) to generate Node Attribute (Binary) Graphs based on the Attraction model introduced by John Skvoretz [2]

## How to Run:
```python SyntheticLabelGen.py <graph dataset> <number of attribute values> <p> <tau>```

## Examples:
```python SyntheticLabelGen.py ./dataset/polblogs.txt 2 0.5 0.25```

## Algorithm
> Let p be proportion of R nodes and so (1-p) is proportion of B nodes.  Random assignment would produce by chance the following proportions p^2 R-R ties, 2p(1-p) R-B ties and (1-p)^2 B-B ties.
 
> There is a tunable parameter 0<=tau<=1 that in an attraction model would produce a distribution of ties with the following proportions
R-R = (tau+(1-tau)p)p
R-B = 2(1-tau)p(1-p)
B-B = (tau+(1-tau(1-p))(1-p)
 
> So idea is to take any structure, randomly assign R and B labels then draw and R node and a B node at random and swap labels if it would decrease the number of R-B ties and stop when the total number of R-B ties = 2(1-tau)p(1-p)*|E| with |E| the number of edges in the network.

## Related Papers:
1. Skvoretz, J., 2013. Diversity, integration, and social ties: Attraction versus repulsion as drivers of intra-and intergroup relations. American Journal of Sociology, 119(2), pp.486-517.
2. Horawalavithana, S., Gandy, C., Flores, J.A., Skvoretz, J. and Iamnitchi, A., 2018, December. Diversity, Homophily and the Risk of Node Re-identification in Labeled Social Graphs. In International Workshop on Complex Networks and their Applications (pp. 400-411). Springer, Cham.
