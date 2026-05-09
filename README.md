##  PRORP

This repository hosts the artifact **PRORP** for the paper **“Mining Statistically Likely $k$-Reachable States in Probabilistic Programs.”**

---

##  What Does PRORP Do?

**PRORP** is a framework for learning ***statistically likely reachable sets*** of probabilistic Boolean programs.

Given:
* a probabilistic program $P$,
* a precondition $\varphi_0$,
* and a loop unrolling bound $k$,

PRORP learns a **propositional (DNF) formula** approximating the set of states reachable from $\varphi_0$ within $\leq k$ steps, with statistical confidence parameters $(\varepsilon, \delta)$.

PRORP integrates:
1. **SAT-based sampling** using [CMSGen](https://github.com/meelgroup/cmsgen),
2. **Decision-tree-based DNF learning**, and
3. **SAT-based counterexample-guided refinement**.

Together, these form a ***sampling–learning–refinement loop*** analogous to CEGIS, but statistically grounded.

---

##  Structure of This Artifact

Our implementation mirrors the PRORP pseudocode presented in the paper and is organized as follows:

| **Module** | **Purpose** |
| :--- | :--- |
| `TreeLearner/` | TreeRepair :- Learns candidate DNF formulas from sampled reachable states |
| `DistEstimate/` | FoRT :- Estimates probabilistic distances between state distributions |
| `Validifier/` | BaRT :- Validates and refines candidate formulas using SAT solvers |
| `progformula/` | Contains CNF encodings of benchmark programs |
| `driver.py` | Orchestrates the PRORP pipeline |
| `run.sh` | Convenience script to launch PRORP |

---

##  Getting Started

We support two setup methods:
*  **Using an existing Docker image** (requires Docker)
*  **Prepare your own Docker image** (requires Docker)
*  **Manual setup** 

---

###  First Method: Using an existing Docker image

#### Step 1: Install Docker on your machine

Follow the official guide for installation ([https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)).

Verify installation by:

```bash
$ docker --version`
```

#### Step 2: Extract and load the Docker image

At the repository root (inside the folder ```PRORP_artifact```), run: 
```bash
$ docker load -i prorp_artifact_v1.tar
```

#### Step 3: Executing the Docker image in a container

Now execute the image by running the command: 
```bash
$ docker run -it --name prorp_container prorp_artifact:v1 /bin/bash
```


###  Second Method: Prepare your own Docker image


Install Docker on your machine by following ```Step 1``` of ```First Method : Using an existing Docker image```.


#### Step 1: Build the Docker image

At the repository root (inside the folder ```PRORP_artifact```), run: 

```bash
$ docker build -t prorp_artifact:v1 .
```
where you can insert your favourite name for the Docker image in place of ```<image_name>```.

#### Step 2: Executing the Docker image in a container


Now execute the image by running the command: 
```bash
$ docker run -it --name prorp_container prorp_artifact:v1 /bin/bash
```




###  Third Method:  Manual Setup


Manual setup is suitable for debugging or modifying components of the PRORP pipeline.

---

#### Step 1: Clone the Repository
```bash
$ git clone https://github.com/arnab-007/BoolProg.git
$ cd BoolProg
```



#### Step 2: Create and Activate a Virtual Environment

Ensure Python $\geq$ 3.10. If venv is not available, run:

```bash
$ sudo apt install python3-venv -y 
$ python3 -m venv .venv 
$ source .venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
$ pip install --upgrade pip 
$ pip install -r requirements.txt
```

#### Step 4: Install external tools like CMSGen and CryptoMiniSat

CryptoMiniSat: 

```bash
$ wget [https://github.com/msoos/cryptominisat/releases/download/release/5.13.0/cryptominisat5-linux-amd64.zip](https://github.com/msoos/cryptominisat/releases/download/release/5.13.0/cryptominisat5-linux-amd64.zip) -O cms.zip 
$ unzip cms.zip 
$ sudo mv cryptominisat5 /usr/local/bin/ 
$ sudo chmod +x /usr/local/bin/cryptominisat5
```


CMSGen: 

```bash
$ wget [https://github.com/meelgroup/cmsgen/releases/download/release/6.1.1/cmsgen-linux-x86_64.zip](https://github.com/meelgroup/cmsgen/releases/download/release/6.1.1/cmsgen-linux-x86_64.zip) -O cmsgen.zip 
$ unzip cmsgen.zip 
$ sudo mv cmsgen /usr/local/bin/ 
$ sudo chmod +x /usr/local/bin/cmsgen
```

Verify the installations: 

```bash
$ which cryptominisat5 
$ which cmsgen
```

## Executing PRORP


Irrespective of manual installation or installation via Docker, navigate to the ```PRORP``` folder inside the repository ```PRORP_artifact``` by running :

```bash
$ cd PRORP/
```

### Method 1: Executing a single benchmark (for early smoke test review)

```bash
$ python3 driver.py <progname> <iters> <epsilon_1> <epsilon_2> <delta> 
```

where ```<proname>``` is the name of the benchmark and ```<iters>``` is the loop unrolling depth. ```<epsilon_1>``` and ```<epsilon_2>``` are the FoRT and BaRT error bounds $\varepsilon_1$ and $\varepsilon_2$ respectively and ```<delta>``` is the confidence parameter $\delta$. The parameters $\varepsilon_1, \varepsilon_1, \delta$ should fall in the range $(0,1]$.


Example for executing a single benchmark :

```bash
$ python3 driver.py LinExp 64 0.05 0.05 0.1 
```

### Method 2: Executing all the benchmarks at once (for full replication of paper results)

```bash
$ python3 driver.py all 
```
---

### License

This project is licensed under the [MIT License](./LICENSE).


