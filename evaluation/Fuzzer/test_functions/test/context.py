import numpy
import scipy.sparse
import os

class MeasureImageOverlap:
    def __init__(self):
        pass

    <<insert solution here>>

def main():
    numpy.random.seed(<|int;range=0,10000|>)
    test_labels = numpy.random.randint(2, size=(10))
    numpy.random.seed(<|int;range=0,10000|>)
    ground_truth_labels = numpy.random.randint(2, size=(10))
    numpy.random.seed(<|int;range=0,10000|>)
    mask = numpy.random.randint(2, size=(10))

    print(MeasureImageOverlap().compute_rand_index(test_labels, ground_truth_labels, mask))

if __name__ == '__main__':
    main()