def compute_rand_index(self, test_labels, ground_truth_labels, mask):
    """Calculate the Rand Index

        http://en.wikipedia.org/wiki/Rand_index

        Given a set of N elements and two partitions of that set, X and Y

        A = the number of pairs of elements in S that are in the same set in
            X and in the same set in Y
        B = the number of pairs of elements in S that are in different sets
            in X and different sets in Y
        C = the number of pairs of elements in S that are in the same set in
            X and different sets in Y
        D = the number of pairs of elements in S that are in different sets
            in X and the same set in Y

        The rand index is:   A + B
                             -----
                            A+B+C+D


        The adjusted rand index is the rand index adjusted for chance
        so as not to penalize situations with many segmentations.

        Jorge M. Santos, Mark Embrechts, "On the Use of the Adjusted Rand
        Index as a Metric for Evaluating Supervised Classification",
        Lecture Notes in Computer Science,
        Springer, Vol. 5769, pp. 175-184, 2009. Eqn # 6

        ExpectedIndex = best possible score

        ExpectedIndex = sum(N_i choose 2) * sum(N_j choose 2)

        MaxIndex = worst possible score = 1/2 (sum(N_i choose 2) + sum(N_j choose 2)) * total

        A * total - ExpectedIndex
        -------------------------
        MaxIndex - ExpectedIndex

        returns a tuple of the Rand Index and the adjusted Rand Index
        """
    ground_truth_labels = ground_truth_labels[mask].astype(numpy.uint32)
    test_labels = test_labels[mask].astype(numpy.uint32)
    if len(test_labels) > 0:
        N_ij = scipy.sparse.coo_matrix((numpy.ones(len(test_labels)), (
            ground_truth_labels, test_labels))).toarray()

        def choose2(x):
            """Compute # of pairs of x things = x * (x-1) / 2"""
            return x * (x - 1) / 2
        A = numpy.sum(choose2(N_ij))
        N_i = numpy.sum(N_ij, 1)
        N_j = numpy.sum(N_ij, 0)
        C = numpy.sum((N_i[:, numpy.newaxis] - N_ij) * N_ij) / 2
        D = numpy.sum((N_j[numpy.newaxis, :] - N_ij) * N_ij) / 2
        total = choose2(len(test_labels))
        B = total - A - C - D
        rand_index = (A + B) / total
        expected_index = numpy.sum(choose2(N_i)) * numpy.sum(choose2(N_j))
        max_index = (numpy.sum(choose2(N_i)) + numpy.sum(choose2(N_j))
            ) * total / 2
        adjusted_rand_index = (A * total - expected_index) / (max_index -
            expected_index)
    else:
        rand_index = adjusted_rand_index = numpy.nan
    return rand_index, adjusted_rand_index