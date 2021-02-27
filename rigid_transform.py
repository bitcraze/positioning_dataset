import numpy as np

# This algorithm is based on the following publication:
#   K. S. Arun, Thomas S. Huang, Steven D. Blostein:
#   Least-Squares Fitting of Two 3-D Point Sets. IEEE Trans. Pattern Anal. Mach. Intell. 9(5): 698-700 (1987)
# Some other resources:
#   http://nghiaho.com/?page_id=671
#   https://en.wikipedia.org/wiki/Kabsch_algorithm
def compute_rigid_transform(A, B):
    assert A.shape == B.shape
    assert A.shape[1] == 3
    assert A.shape[0] > 3

    centroid_A = np.mean(A, axis=0)
    centroid_B = np.mean(B, axis=0)

    # compute rotation
    H = (A-centroid_A).T @ (B-centroid_B)
    U,S,Vt = np.linalg.svd(H)
    V = Vt.T

    d = np.sign(np.linalg.det(V @ U.T))
    R = V @ np.diag([1,1,d]) @ U.T

    t = -R @ centroid_A + centroid_B
    return R, t


if __name__ == "__main__":
    import rowan

    A = np.random.sample((1000,3))
    
    # compute random rotation and translation
    R = rowan.to_matrix(rowan.random.random_sample())
    t = np.random.sample(3)

    # generate noise
    noise = np.random.normal(loc=0.0, scale=0.01, size=A.shape)

    # apply rotation
    B = A @ R.T + t + noise

    R_computed, t_computed = compute_rigid_transform(A, B)
    print(R)
    print(R_computed)
    assert np.allclose(R, R_computed, 1e-2)
    assert np.allclose(t, t_computed, 1e-2)
