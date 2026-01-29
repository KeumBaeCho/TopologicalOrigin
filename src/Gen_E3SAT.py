"""
Gen_E-3SAT.py
E-3SAT Instance Generator using TBL-MRE (Toroidal Binomial Lattice with Modular Random Encapsulation)

This module implements the deterministic construction from the paper:
"Topological Origins of Computational Hardness"
"""

import random
import struct
from typing import List, Tuple
from math import comb


class Clause:
    """Represents a 3-CNF clause with three literals"""
    def __init__(self, dl=0, sl=0, rl=0):
        self.dl = dl  # dominant literal
        self.sl = sl  # switching literal
        self.rl = rl  # random literal
    
    def __repr__(self):
        return f"Clause(dl={self.dl}, sl={self.sl}, rl={self.rl})"
    
    def to_list(self):
        """Convert clause to list of literals"""
        return [self.dl, self.sl, self.rl]


class Node:
    """Represents a TBL node containing two clauses sharing a dominant literal"""
    def __init__(self):
        self.c1 = Clause()
        self.c2 = Clause()


class E3SATGenerator:
    """E-3SAT instance generator using TBL-MRE construction"""
    
    def __init__(self, seed=None):
        """Initialize generator with optional random seed"""
        if seed is not None:
            random.seed(seed)
    
    @staticmethod
    def shuffle_array(array):
        """Shuffle array randomly"""
        arr = array.copy()
        for _ in range(len(arr)):
            random1 = random.randint(0, len(arr) - 1)
            random2 = random.randint(0, len(arr) - 1)
            arr[random1], arr[random2] = arr[random2], arr[random1]
        return arr
    
    @staticmethod
    def make_toroidal_tree(dl: List[int], column_size: int, 
                          level_size: int,
                          k_seed: int = None) -> List[List[Node]]:
        """
        Generate Toroidal tree with Level-Shifted Binomial Stride
        
        Args:
            dl: Dominant literal array
            column_size: Number of columns (N_col)
            level_size: Number of levels
            k_seed: Seed for binomial coefficient calculation
        
        Returns:
            2D array of Nodes representing the toroidal lattice
        """
        if len(dl) != column_size * level_size:
            return None
        
        # Initialize 2D array
        ret = [[Node() for _ in range(level_size)] for _ in range(column_size)]
        
        # 1. Fill dominant literal in tree
        for i in range(column_size):
            for j in range(level_size):
                ret[i][j].c1.dl = ret[i][j].c2.dl = dl[i * level_size + j]
        
        # 2. Fill switching variable with double rounding
        for i in range(column_size):
            for j in range(level_size):
                ret[i][j].c1.sl = -1 * ret[i][(j + 1) % level_size].c1.dl
                ret[i][j].c2.sl = -1 * ret[(i + 1) % column_size][(j + 1) % level_size].c2.dl
        
        # 3. Assign random variable with Level-Shifted Binomial Stride
        for i in range(column_size):
            # Calculate distance for current level using binomial stride
            distance = max(2, column_size // 2 - 1)
            
            # Get dominant literal group from target column
            target_column = (i + distance) % column_size
            dl_group = [ret[target_column][j].c1.dl for j in range(level_size)]
            
            # Shuffle for c2.rl
            dl_group = E3SATGenerator.shuffle_array(dl_group)
            for j in range(level_size):
                ret[i][j].c2.rl = dl_group[j]
            
            # Ensure c1.rl and c2.rl don't have same variable at same position
            check = False
            while not check:
                dl_group = E3SATGenerator.shuffle_array(dl_group)
                check = True
                for j in range(level_size):
                    if dl_group[j] == ret[i][j].c2.rl:
                        check = False
                        break
            
            # Assign negated literals to c1.rl
            for j in range(level_size):
                ret[i][j].c1.rl = -1 * dl_group[j]
        
        return ret
    
    def generate_instance(self, private_key: List[bool], column_size: int, 
                         level_size: int, num_tree: int = 2, 
                         k_seed: int = None) -> Tuple[List[Clause], dict]:
        """
        Generate E-3SAT instance using TBL-MRE construction
        
        Args:
            private_key: Boolean array representing the basis solution
            column_size: Number of columns in the toroidal lattice
            level_size: Number of levels in the toroidal lattice
            num_tree: Number of trees (1 or 2 for dual construction)
            k_seed: Seed for binomial coefficient calculation
        
        Returns:
            Tuple of (clause list, metadata dict)
        """
        if len(private_key) != column_size * level_size:
            raise ValueError("Private key length must equal column_size × level_size")
        if num_tree not in [1, 2]:
            raise ValueError("num_tree must be 1 or 2")
        
        private_key_size = len(private_key)
        dl_true_tree = []
        dl_false_tree = []
        
        # Generate dominant literal for True/False tree
        for i in range(private_key_size):
            if private_key[i]:
                dl_true_tree.append(i + 1)
            else:
                dl_true_tree.append(-(i + 1))
            dl_false_tree.append(-1 * dl_true_tree[i])
        
        # Shuffle arrays
        dl_true_tree = self.shuffle_array(dl_true_tree)
        dl_false_tree = self.shuffle_array(dl_false_tree)
        
        # Generate Toroidal tree with binomial stride option
        true_tree = self.make_toroidal_tree(
            dl_true_tree, column_size, level_size, k_seed
        )
        false_tree = self.make_toroidal_tree(
            dl_false_tree, column_size, level_size, k_seed
        )
        
        # Generate total clauses array
        total_clauses = []
        
        # Add clauses from True tree
        for i in range(column_size):
            for j in range(level_size):
                total_clauses.append(true_tree[i][j].c1)
                total_clauses.append(true_tree[i][j].c2)
        
        # Add clauses from False tree if num_tree is 2
        if num_tree == 2:
            for i in range(column_size):
                for j in range(level_size):
                    total_clauses.append(false_tree[i][j].c1)
                    total_clauses.append(false_tree[i][j].c2)
        
        # Shuffle clauses to remove structural patterns
        total_clauses = self.shuffle_array(total_clauses)
        
        # Prepare metadata
        metadata = {
            'num_variables': private_key_size,
            'num_clauses': len(total_clauses),
            'column_size': column_size,
            'level_size': level_size,
            'num_tree': num_tree,
            'k_seed': k_seed,
            'basis_solution': private_key.copy()
        }
        
        return total_clauses, metadata
    
    @staticmethod
    def clauses_to_cnf_string(clauses: List[Clause], num_variables: int) -> str:
        """
        Convert clauses to DIMACS CNF format string
        
        Args:
            clauses: List of Clause objects
            num_variables: Number of variables
        
        Returns:
            CNF string in DIMACS format
        """
        lines = []
        lines.append(f"p cnf {num_variables} {len(clauses)}")
        for clause in clauses:
            lines.append(f"{clause.dl} {clause.sl} {clause.rl} 0")
        return "\n".join(lines)
    
    @staticmethod
    def clauses_to_pysat_format(clauses: List[Clause]) -> List[List[int]]:
        """
        Convert clauses to PySAT format (list of lists)
        
        Args:
            clauses: List of Clause objects
        
        Returns:
            List of clauses in PySAT format
        """
        return [clause.to_list() for clause in clauses]
    
    @staticmethod
    def convert_clause_to_byte(clauses: List[Clause]) -> bytes:
        """Convert Clause list to bytes for storage/transmission"""
        result = bytearray()
        for clause in clauses:
            result.extend(struct.pack('<h', clause.dl))
            result.extend(struct.pack('<h', clause.sl))
            result.extend(struct.pack('<h', clause.rl))
        return bytes(result)
    
    @staticmethod
    def convert_byte_to_clause(data: bytes) -> List[Clause]:
        """Convert bytes to Clause list"""
        clauses = []
        for i in range(0, len(data), 6):
            clause = Clause()
            clause.dl = struct.unpack('<h', data[i:i+2])[0]
            clause.sl = struct.unpack('<h', data[i+2:i+4])[0]
            clause.rl = struct.unpack('<h', data[i+4:i+6])[0]
            clauses.append(clause)
        return clauses


def generate_random_private_key(size: int) -> List[bool]:
    """Generate a random private key (basis solution)"""
    return [random.choice([True, False]) for _ in range(size)]


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("E-3SAT Generator using TBL-MRE Construction")
    print("=" * 60)
    print()
    
    # Parameters
    level_size = 6
    column_size = 6
    n = level_size * column_size  # Number of variables
    
    print(f"Parameters:")
    print(f"  Level size: {level_size}")
    print(f"  Column size: {column_size}")
    print(f"  Number of variables: {n}")
    print()
    
    # Generate random private key
    private_key = generate_random_private_key(n)
    print(f"Private key (first 10): {private_key[:10]}")
    print()
    
    # Create generator
    generator = E3SATGenerator(seed=42)
    
    # Generate E-3SAT instance
    clauses, metadata = generator.generate_instance(
        private_key=private_key,
        column_size=column_size,
        level_size=level_size,
        num_tree=2,  # Dual construction
        k_seed=4
    )
    
    print(f"Generated E-3SAT instance:")
    print(f"  Number of clauses: {metadata['num_clauses']}")
    print(f"  Number of variables: {metadata['num_variables']}")
    print()
    
    # Show first few clauses
    print("First 5 clauses:")
    for i, clause in enumerate(clauses[:5]):
        print(f"  Clause {i+1}: {clause.to_list()}")
    print()
    
    # Convert to different formats
    print("Export formats:")
    
    # 1. DIMACS CNF format
    cnf_string = E3SATGenerator.clauses_to_cnf_string(clauses, n)
    print(f"  DIMACS CNF: {len(cnf_string)} bytes")
    
    # 2. PySAT format
    pysat_clauses = E3SATGenerator.clauses_to_pysat_format(clauses)
    print(f"  PySAT format: {len(pysat_clauses)} clauses")
    
    # 3. Binary format
    binary_data = E3SATGenerator.convert_clause_to_byte(clauses)
    print(f"  Binary format: {len(binary_data)} bytes")
    print()
    
    print("Generation complete!")
