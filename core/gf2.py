"""GF(2) manipulation functions"""

import numpy as np

type SHAPE_2D = tuple[int, int]
type SHAPE_1D = int
type GF2_INT = np.dtype[np.uint8]
type GF2_MATRIX = np.ndarray[SHAPE_2D, GF2_INT]
type GF2_VECTOR = np.ndarray[SHAPE_1D, GF2_INT]


def int_to_gf2vec(integer: int, size: int) -> GF2_VECTOR:
    """Convert integer to GF(2) bit-vector"""
    return np.array(tuple((integer >> i) & 1 for i in range(size)), np.uint8)


def gf2vec_to_int(gf2vec: GF2_VECTOR) -> int:
    """Convert GF(2) bit-vector to integer"""
    integer = 0
    size = len(gf2vec) - 1
    for bit in gf2vec:
        integer >>= 1
        integer |= int(bit) << size
    return integer


def resize(mat: GF2_MATRIX, new_shape: SHAPE_2D) -> GF2_MATRIX:
    """Copy and resize a GF(2) matrix"""
    mat_rows, mat_cols = mat.shape
    new_rows, new_cols = new_shape
    new_mat = np.zeros(new_shape, np.uint8)
    new_mat[: min(mat_rows, new_rows), : min(mat_cols, new_cols)] = mat[
        : min(mat_rows, new_rows), : min(mat_cols, new_cols)
    ]
    return new_mat


def echelon(
    mat: GF2_MATRIX,
) -> tuple[GF2_MATRIX, GF2_MATRIX, int, list[int]]:
    """Compute reduced row echelon form of a GF(2) matrix"""
    rows, columns = mat.shape
    echelon_mat = np.copy(mat)
    transform_mat = np.identity(rows, np.uint8)
    rank = 0
    pivots = []

    for j in range(columns):
        for i in range(rank, rows):
            if echelon_mat[i, j]:
                for k in range(rows):
                    if (k != i) and echelon_mat[k, j]:
                        echelon_mat[k] ^= echelon_mat[i]
                        transform_mat[k] ^= transform_mat[i]
                echelon_mat[[i, rank]] = echelon_mat[[rank, i]]
                transform_mat[[i, rank]] = transform_mat[[rank, i]]
                pivots.append(j)
                rank += 1
                break

    return echelon_mat, transform_mat, rank, pivots


def generalized_inverse(mat: GF2_MATRIX) -> GF2_MATRIX:
    """Compute the Moore-Penrose inverse of a GF(2) matrix"""
    _, transform_mat, rank, pivots = echelon(mat)
    transform_mat = resize(transform_mat, (mat.shape[1], mat.shape[0]))
    for i in range(rank - 1, -1, -1):
        column_index = pivots[i]
        transform_mat[[i, column_index]] = transform_mat[[column_index, i]]
    return transform_mat


def left_nullbasis(mat: GF2_MATRIX) -> GF2_MATRIX:
    """Compute the left-nullbasis of a GF(2) matrix"""
    mat_inv = generalized_inverse(mat)
    basis: GF2_MATRIX = mat @ mat_inv
    basis = basis + np.identity(basis.shape[0], np.uint8)
    echelon_mat, _, rank, _ = echelon(basis & np.uint8(1))
    return echelon_mat[:rank]


def apply_left_nullspace(
    nullbasis: GF2_MATRIX, principal_solution: GF2_VECTOR, key: int
) -> GF2_VECTOR:
    """Apply left-nullspace vector from key to principal solution"""
    solution = np.copy(principal_solution)
    for i in range(nullbasis.shape[0]):
        if (key >> i) & 1:
            solution ^= nullbasis[i]
    return solution
