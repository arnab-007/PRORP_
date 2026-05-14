import pandas as pd
from collections import Counter, defaultdict
from sklearn import tree
import numpy as np
import random
import matplotlib.pyplot as plt
import time

# from graphviz import Digraph
import pickle
from collections import deque


class Node:
    def __init__(
        self,
        feature=None,
        lchild=None,
        rchild=None,
        value=None,
        threshold=None,
        node_id=None,
    ) -> None:
        self.feature = feature
        self.lchild = lchild
        self.rchild = rchild
        self.threshold = threshold
        self.node_id = node_id
        self.value = value
        self.datapoints = pd.DataFrame()

    def is_leaf_node(self):
        return self.value is not None


class CustomDecisionTree:
    def __init__(self, min_samples_split=2, max_depth=100) -> None:
        self.min_samples_split = min_samples_split
        self.max_depth = max_depth
        self.root = None
        self.node_counter = 0
        # #self.features_used = set() # this will get updated while building the tree, while applying pruning and split mutation.

    def fit_initial(self, X, y, weights, feature_names=None):
        self.feature_names = (
            feature_names
            if feature_names is not None
            else [f"feature_{i}" for i in range(X.shape[1])]
        )

        clf = tree.DecisionTreeClassifier(
            criterion="entropy",
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            random_state=0,
        )
        print("Starting model fitting...")
        start_time = time.time()
        clf = clf.fit(X, y, sample_weight=weights)
        print(f"--- Fitting took: {time.time() - start_time:.4f} seconds ---")
        # with open('decision_tree_model.pkl', 'rb') as f:
        #     clf = pickle.load(f)
        # plt.figure(figsize=(20,10))
        # tree.plot_tree(clf, filled=True, feature_names=self.feature_names, class_names=['0', '1'], rounded=True, fontsize=14)
        # plt.show()
        print("Starting custom tree build...")
        start_time = time.time()
        self.root = self.build_tree(clf)
        print(f"--- Custom tree build took: {time.time() - start_time:.4f} seconds ---")

    def build_tree(self, clf):
        """
        Builds a tree by traversing the decision tree learned by scikit-learn using breadth-first traversal.

        Parameters:
        clf: DecisionTreeClassifier
            The trained decision tree classifier from scikit-learn.

        Returns:
        Node
            The root node of the tree built from the classifier.
        """
        # Get the attributes of the trained classifier
        children_left = clf.tree_.children_left
        children_right = clf.tree_.children_right
        feature = clf.tree_.feature
        threshold = clf.tree_.threshold
        value = clf.tree_.value

        # Define a queue to manage nodes for breadth-first traversal
        from collections import deque

        queue = deque()

        # Create the root node and enqueue it
        root = Node(feature=None, threshold=None, lchild=None, rchild=None, node_id=1)
        queue.append(
            (root, 0, "1")
        )  # (Node object, scikit-learn node ID, hierarchical node ID)

        while queue:
            current_node, sklearn_node_id, hierarchical_id = queue.popleft()

            if (
                children_left[sklearn_node_id] == -1
                and children_right[sklearn_node_id] == -1
            ):
                # Leaf node
                current_node.value = value[sklearn_node_id].argmax()
                continue

            # Internal node
            current_node.feature = feature[sklearn_node_id]
            current_node.threshold = threshold[sklearn_node_id]

            # Create left child
            if children_left[sklearn_node_id] != -1:
                left_id = f"{hierarchical_id}1"
                left_child = Node(
                    feature=None,
                    threshold=None,
                    lchild=None,
                    rchild=None,
                    node_id=int(left_id),
                )
                current_node.lchild = left_child
                queue.append((left_child, children_left[sklearn_node_id], left_id))

            # Create right child
            if children_right[sklearn_node_id] != -1:
                right_id = f"{hierarchical_id}2"
                right_child = Node(
                    feature=None,
                    threshold=None,
                    lchild=None,
                    rchild=None,
                    node_id=int(right_id),
                )
                current_node.rchild = right_child
                queue.append((right_child, children_right[sklearn_node_id], right_id))

        return root

    def predict_old(self, X, expected_labels=None, weights=None, member=None):
        if expected_labels is None or weights is None or member is None:
            raise ValueError(
                "Expected labels, weights and member identifier are required since predicted data points will be stored in the leaf nodes."
            )
        # for x, exl, wt in zip(X, expected_labels, weights):
        #     print(predict_and_store(x, exl, wt, self.root, self.feature_names))
        return np.array(
            [
                predict_and_store(x, exl, wt, dist, self.root, self.feature_names)
                for x, exl, wt, dist in zip(X, expected_labels, weights, member)
            ]
        )

    def _batch_update_leaves(self, new_data_for_leaves):
        """
        Updates leaf nodes with new data in a single batch operation per leaf,
        including the precise conflict detection logic.
        """
        for node, new_points_list in new_data_for_leaves.items():
            if not new_points_list:
                continue

            new_data_df = pd.DataFrame(
                new_points_list,
                columns=list(self.feature_names) + ["label", "weight", "member"],
            )

            # 1. Concatenate old and new dataframes
            # node.datapoints = pd.concat([node.datapoints, new_data_df], ignore_index=True)
            node.datapoints = new_data_df

            # 2. Drop duplicates based on all columns except weight
            # node.datapoints.drop_duplicates(
            #     subset=[col for col in node.datapoints.columns if col != "weight"],
            #     inplace=True,
            # )

            # 3. YOUR ORIGINAL, CORRECT CONFLICT CHECK
            # This is now performed efficiently once per updated leaf.
            feature_cols = [
                col
                for col in node.datapoints.columns
                if col not in ("weight", "label", "member")
            ]
            grouped = node.datapoints.groupby(feature_cols)
            for key, group in grouped:
                if group["member"].nunique() > 1:
                    print("Conflict detected for feature values:", key)
                    print(group)
                    raise ValueError(
                        "Conflict: Same datapoint with different 'member' values detected!"
                    )

            # 4. Update the node's predicted value
            node.value = most_common_label(node.datapoints["label"].values)

    def predict(self, X, expected_labels=None, weights=None, member=None):
        if expected_labels is None or weights is None or member is None:
            raise ValueError(
                "Expected labels, weights and member identifier are required."
            )

        # A dictionary to buffer new data for each leaf node
        new_data_for_leaves = defaultdict(list)
        predictions = []

        # === Part 1: Fast Prediction and Collection ===
        # This loop is fast. It only finds the leaf and appends to lists.
        for x, exl, wt, dist in zip(X, expected_labels, weights, member):
            # 1. Find the destination leaf node for the current point 'x'
            leaf_node = _find_leaf_node(x, self.root)

            # 2. The prediction is the current value of the leaf BEFORE it's updated
            predictions.append(leaf_node.value)

            # 3. Buffer the new data in a simple list. No DataFrames yet!
            new_data_for_leaves[leaf_node].append(np.append(x, [exl, wt, dist]))

        # === Part 2: Batch Update ===
        # Now, process the buffered data in one efficient go.
        self._batch_update_leaves(new_data_for_leaves)

        return np.array(predictions)

    # def save_tree(self, output_file="tree"):
    #     # dot = Digraph(format='svg')
    #     # build_graph(dot, self.root, self.feature_names)
    #     # dot.render(output_file, cleanup=True)
    #     dot = Digraph(format="png")
    #     build_graph(dot, self.root, self.feature_names)
    #     dot.render(output_file, cleanup=True)

    def print_leaf_datapoints(self):
        print_leaf_data(self.root)

    def collect_all_data(self):
        return collect_all_datapoints(self.root)

    def get_tree_snapshot(self):
        tree_nodes = []
        tree_nodes.append((None, self.root.feature, 1))
        return tree_snapshot(self.root, tree_nodes)

    def prune_node(self, node_id_to_prune):
        node_to_prune, parent, _ = find_node_and_parent(
            self.root, node_id_to_prune, set()
        )
        if node_to_prune is None or not node_to_prune.is_leaf_node():
            raise ValueError(
                f"Cannot prune a node that is not a leaf node or does not exist."
            )

        sibling = (
            parent.lchild
            if parent and parent.rchild == node_to_prune
            else parent.rchild if parent else None
        )
        _, grandparent, _ = (
            find_node_and_parent(self.root, parent.node_id, set())
            if parent
            else (None, None, None)
        )
        """I will have two cases here:
        1) If grandparent is None then the sibling is the root node.
        2) If grandparent is not None then the sibling is the child of the grandparent.
        Now predict the data points of the pruned node and update the node ids and features.
        Corner Case: If parent is None, then the node to prune is the root node and that should not be pruned."""

        if parent is None:
            raise ValueError(f"Cannot prune the root node.")
        elif grandparent is None:
            self.root = sibling
        else:
            if grandparent.lchild == parent:
                grandparent.lchild = sibling
            else:
                grandparent.rchild = sibling
        if node_to_prune.datapoints.shape[0] > 0:
            self.predict(
                node_to_prune.datapoints[self.feature_names].values,
                expected_labels=node_to_prune.datapoints["label"].values,
                weights=node_to_prune.datapoints["weight"].values,
                member=node_to_prune.datapoints["member"].values,
            )
        update_node_ids(self.root)

    def split_node_bounds(self, node_id_to_split):
        """Splitting a leaf node is simple than pruning a leaf node:
        1) Find the node to split, now use the node datapoints to find a new split while tracking not to use the same feature again.
        2) Create two new nodes, one for left and one for right."""
        # used_features = set()
        node_to_split, parent, used_features = find_node_and_parent(
            self.root, node_id_to_split, set()
        )
        if node_to_split is None or not node_to_split.is_leaf_node():
            raise ValueError(
                f"Cannot split a node that is not a leaf node or does not exist."
            )
        if len(node_to_split.datapoints) < 2:
            raise ValueError(f"Cannot split a node that has less than 2 data points.")

        leaf_data = node_to_split.datapoints
        leaf_value = most_common_label(leaf_data["label"].values)
        error0 = leaf_data[
            (leaf_data["member"] == 0) & (leaf_data["label"] != leaf_value)
        ].weight.sum()
        error1 = leaf_data[
            (leaf_data["member"] == 1) & (leaf_data["label"] != leaf_value)
        ].weight.sum()

        best_feature, best_threshold = best_split(
            node_to_split.datapoints[self.feature_names].values,
            node_to_split.datapoints["label"].values,
            node_to_split.datapoints["weight"].values,
            len(self.feature_names),
            used_features,
        )
        # print(best_feature)
        if best_feature is None:
            raise ValueError("No feature found that can further split the node.")

        left_indices = (
            node_to_split.datapoints[self.feature_names].values[:, best_feature]
            <= best_threshold
        )
        left_data = node_to_split.datapoints[left_indices]
        right_data = node_to_split.datapoints[~left_indices]
        left_value = most_common_label(left_data["label"].values)
        right_value = most_common_label(right_data["label"].values)
        error0l = left_data[
            (left_data["member"] == 0) & (left_data["label"] != left_value)
        ].weight.sum()
        error1l = left_data[
            (left_data["member"] == 1) & (left_data["label"] != left_value)
        ].weight.sum()
        error0r = right_data[
            (right_data["member"] == 0) & (right_data["label"] != right_value)
        ].weight.sum()
        error1r = right_data[
            (right_data["member"] == 1) & (right_data["label"] != right_value)
        ].weight.sum()
        gainvalid = error0 - (error0l + error0r)
        gaindist = error1 - (error1l + error1r)
        return gainvalid, gaindist

    def split_node(self, node_id_to_split):
        """Splitting a leaf node is simple than pruning a leaf node:
        1) Find the node to split, now use the node datapoints to find a new split while tracking not to use the same feature again.
        2) Create two new nodes, one for left and one for right."""
        # used_features = set()
        node_to_split, parent, used_features = find_node_and_parent(
            self.root, node_id_to_split, set()
        )
        if node_to_split is None or not node_to_split.is_leaf_node():
            raise ValueError(
                f"Cannot split a node that is not a leaf node or does not exist."
            )
        if len(node_to_split.datapoints) < 2:
            raise ValueError(f"Cannot split a node that has less than 2 data points.")
        best_feature, best_threshold = best_split(
            node_to_split.datapoints[self.feature_names].values,
            node_to_split.datapoints["label"].values,
            node_to_split.datapoints["weight"].values,
            len(self.feature_names),
            used_features,
        )
        # print(best_feature)
        if best_feature is None:
            raise ValueError("No feature found that can further split the node.")

        left_indices = (
            node_to_split.datapoints[self.feature_names].values[:, best_feature]
            <= best_threshold
        )
        left = Node(
            value=most_common_label(
                node_to_split.datapoints["label"].values[left_indices]
            ),
            node_id=node_id_to_split * 10 + 1,
        )
        right = Node(
            value=most_common_label(
                node_to_split.datapoints["label"].values[~left_indices]
            ),
            node_id=node_id_to_split * 10 + 2,
        )
        left.datapoints = node_to_split.datapoints[left_indices]
        right.datapoints = node_to_split.datapoints[~left_indices]
        new_node = Node(
            feature=best_feature,
            threshold=best_threshold,
            lchild=left,
            rchild=right,
            node_id=node_id_to_split,
        )
        """If parent is None, then the node to split is the root node."""
        if parent is None:
            self.root = new_node
            return None, best_feature
        elif parent.lchild == node_to_split:
            parent.lchild = new_node
            return parent.feature, best_feature
        else:
            parent.rchild = new_node
            return parent.feature, best_feature
        # self.save_tree(output_file='aftersplitting1')
        # self.node_counter = update_node_ids(self.root, 0)

    def get_error_bounds(self) -> dict:
        """Traverse all leaf nodes and calculate the error bounds for each leaf node for both member (0 and 1) seperately."""
        valid_error, dist_error = calculated_bounds(self.root)
        return {"dist_error": dist_error, "valid_error": valid_error}

    def get_all_leaf_nodes(self):
        return get_leaf_nodes(self.root)

    def if_exists_dnf(self):
        return exists_dnf(self.root)

    def tree_to_dnf(self):
        paths = []

        def find_paths(node, path):
            if node.is_leaf_node():
                if node.value == 1:
                    paths.append(path)
                return

            if node.lchild is not None:
                find_paths(node.lchild, path + [f"!{self.feature_names[node.feature]}"])
            if node.rchild is not None:
                find_paths(node.rchild, path + [f"{self.feature_names[node.feature]}"])

        find_paths(self.root, [])
        dnf_formula = " || ".join([" && ".join(conditions) for conditions in paths])
        terms = dnf_formula.split("||")
        formatted_terms = [f"({term.strip()})" for term in terms]
        dnf_str = " || ".join(formatted_terms)
        if dnf_str == "()":
            if exists_dnf(self.root):
                dnf_str = f"{self.feature_names[0]} || !{self.feature_names[0]}"
            else:
                dnf_str = f"{self.feature_names[0]} && !{self.feature_names[0]}"

        return dnf_str

    def drop_leaf_datapoints(self, member=None):
        """Drop the data points with member 0 from the leaf nodes."""
        if member is None:
            drop_datapoints(self.root, 0)
            drop_datapoints(self.root, 1)
        elif member == 0:
            drop_datapoints(self.root, 0)
        elif member == 1:
            drop_datapoints(self.root, 1)
        else:
            raise ValueError("Member value should be 0 or 1.")


def drop_datapoints(node, member):
    if node is None:
        return
    if node.is_leaf_node():
        if len(node.datapoints) == 0:
            return
        node.datapoints = node.datapoints[node.datapoints["member"] == 1 - member]
        return
    drop_datapoints(node.lchild, member)
    drop_datapoints(node.rchild, member)


def get_leaf_nodes(node):
    if node is None:
        return []
    if node.is_leaf_node():
        return [node.node_id]
    return get_leaf_nodes(node.lchild) + get_leaf_nodes(node.rchild)


def exists_dnf(node):
    """Check if a node is a leaf node and has data points."""
    if node is None:
        raise ValueError("Node is None. Cannot check for DNF.")
    if node.is_leaf_node():
        return node.value == 1 and len(node.datapoints) > 0
    return exists_dnf(node.lchild) or exists_dnf(node.rchild)


def calculate_pr(node):
    if node is None:
        raise ValueError("Node is None. Cannot calculate confusion.")

    # These will store cumulative TP, FP, TN, FN across all leaves
    TP_total, FP_total, TN_total, FN_total = 0.0, 0.0, 0.0, 0.0

    # Inner recursive DFS
    def dfs(current_node):
        nonlocal TP_total, FP_total, TN_total, FN_total

        if current_node.is_leaf_node():
            if len(current_node.datapoints) == 0:
                return

            datapoints = current_node.datapoints

            # True Positive (predicted 1, true member 1)
            TP_total += datapoints[
                (datapoints["member"] == 1) & (current_node.value == 1)
            ]["weight"].sum()
            # False Positive (predicted 1, true member 0)
            FP_total += datapoints[
                (datapoints["member"] == 0) & (current_node.value == 1)
            ]["weight"].sum()
            # True Negative (predicted 0, true member 0)
            TN_total += datapoints[
                (datapoints["member"] == 0) & (current_node.value == 0)
            ]["weight"].sum()
            # False Negative (predicted 0, true member 1)
            FN_total += datapoints[
                (datapoints["member"] == 1) & (current_node.value == 0)
            ]["weight"].sum()

        else:
            dfs(current_node.lchild)
            dfs(current_node.rchild)

    # Start DFS traversal
    dfs(node)

    # Now calculate final precision and recall
    precision = TP_total / (TP_total + FP_total) if (TP_total + FP_total) > 0 else 0.0
    recall = TP_total / (TP_total + FN_total) if (TP_total + FN_total) > 0 else 0.0

    return ({"precision": precision, "recall": recall},)


def calculated_bounds(node):

    if node is None:
        raise ValueError("Node is None. Cannot calculate error bounds.")
    if node.is_leaf_node():
        if len(node.datapoints) == 0:
            return 0, 0
        """error0 is the sum of the weights of the datapoints (with member 0) that are not equal to the most common label in the leaf node."""
        error0 = node.datapoints[
            (node.datapoints["member"] == 0) & (node.datapoints["label"] != node.value)
        ].weight.sum()
        error1 = node.datapoints[
            (node.datapoints["member"] == 1) & (node.datapoints["label"] != node.value)
        ].weight.sum()
        return error0, error1
    else:
        error0_l, error1_l = calculated_bounds(node.lchild)
        error0_r, error1_r = calculated_bounds(node.rchild)
        return error0_l + error0_r, error1_l + error1_r


# def update_node_ids(node, node_counter):
#     if node is None:
#         raise ValueError('Node is None. Cannot update node ids and features.')
#     node.node_id = node_counter
#     node_counter += 1
#     if not node.is_leaf_node():
#         #features_used.add(feature_names[node.feature])
#         node_counter = update_node_ids(node.lchild, node_counter)
#         node_counter = update_node_ids(node.rchild, node_counter)

#     return node_counter


def update_node_ids(root):
    if root is None:
        raise ValueError("Root node is None. Cannot update node ids.")

    # Use a queue to traverse the tree in BFS order
    queue = deque([(root, 1)])  # Start with the root and its node_id as 1

    while queue:
        node, node_id = queue.popleft()
        node.node_id = node_id  # Assign the current node's id

        # Add left and right children to the queue with their computed node_ids
        if node.lchild:
            queue.append((node.lchild, node_id * 10 + 1))
        if node.rchild:
            queue.append((node.rchild, node_id * 10 + 2))


def find_node_and_parent(node, node_id, used_features, parent=None):
    if node is None:
        return (None, None, None)
    if not node.is_leaf_node():
        used_features.add(node.feature)
    if node.node_id == node_id:
        return (node, parent, used_features)

    # Search in the left child
    result = find_node_and_parent(node.lchild, node_id, used_features, node)
    if result[0] is not None:  # If the node is found
        return result

    # Search in the right child
    result = find_node_and_parent(node.rchild, node_id, used_features, node)
    if result[0] is not None:  # If the node is found
        return result

    if not node.is_leaf_node():
        used_features.remove(node.feature)

    return (None, None, None)


# def find_node_and_parent(node, node_id, used_features, parent=None):
#     if node is None:
#         return (None, None, None)
#     if not node.is_leaf_node():
#         used_features.add(node.feature)
#     if node.node_id == node_id:
#         return (node, parent, used_features)
#     find_node_and_parent(node.lchild, node_id, used_features, node)
#     find_node_and_parent(node.rchild, node_id, used_features, node)
#     if not node.is_leaf_node():
#         used_features.remove(node.feature)

# if node is None:
#     return None, None, None
# if not node.is_leaf_node():
#     used_features.add(node.feature)
# if node.node_id == node_id:
#     return node, parent, used_features
# left_result = find_node_and_parent(node.lchild, node_id, used_features, node)
# if left_result[0] is not None:
#     return left_result
# return find_node_and_parent(node.rchild, node_id, used_features, node)


def print_leaf_data(node):
    if node.is_leaf_node():
        print(
            f"Leaf Node ID: {node.node_id} - Predicted Value: {node.value}, Data Points:\n{node.datapoints}\n"
        )
    else:
        print_leaf_data(node.lchild)
        print_leaf_data(node.rchild)


def collect_all_datapoints(node):

    collected_data = []  # list to store DataFrames

    def dfs(current_node):
        if current_node.is_leaf_node():
            collected_data.append(current_node.datapoints)
        else:
            dfs(current_node.lchild)
            dfs(current_node.rchild)

    dfs(node)  # Start DFS from the root node
    if collected_data:
        return pd.concat(collected_data, ignore_index=True)
    else:
        return pd.DataFrame()  # Return empty if no leaf found


def tree_snapshot(node, tree_nodes=[]):
    """Instead of just having node feature and node id, I will have a tuple of (parents feature ,nodes feature, node_id) for each node."""
    # tree_nodes.append((None, None, node.node_id))
    if node.is_leaf_node():
        return tree_nodes
    tree_nodes.append((node.feature, node.lchild.feature, node.lchild.node_id))
    tree_nodes.append((node.feature, node.rchild.feature, node.rchild.node_id))
    tree_snapshot(node.lchild, tree_nodes)
    tree_snapshot(node.rchild, tree_nodes)
    return tree_nodes


def binary_to_decimal_original(df):
    # Select all columns except the last three: 'label', 'weight', 'member'
    binary_columns = df.iloc[:, :-3]

    # Convert each row of binary values to a decimal number
    decimal_list = binary_columns.apply(
        lambda row: int("".join(row.astype(str)), 2), axis=1
    )

    # Return the list of decimal numbers
    return list(decimal_list)


def binary_to_decimal(df):
    # Select all columns except the last three: 'label', 'weight', 'member'
    binary_columns = df.iloc[:, 9:17]

    # Convert each row of binary values to a decimal number
    decimal_list = binary_columns.apply(
        # lambda row: int("".join(row.astype(str)), 2), axis=1
        lambda row: int("".join(row.astype(int).astype(str)), 2)
    )

    # Return the list of decimal numbers
    return list(decimal_list)


def build_graph(dot, node, feature_names, depth=0):
    if node is None:
        return

    if node.is_leaf_node():
        # Add a leaf node with its value
        # bits = node.datapoints.values  # Shape: (n_rows, n_bits)
        # decimals = [binary_to_decimal(row) for row in bits]
        # dot.node(str(node.node_id), f"node_id={node.node_id}\nLabel: {node.value}\nSamples: {','.join(map(str, decimals))}", shape='box')

        if int(node.value) == 1:
            dot.node(
                str(node.node_id),
                f"node_id={node.node_id}\nLabel: {node.value}\n Samples:{','.join(map(str, binary_to_decimal(node.datapoints)))}",
                shape="box",
            )

        else:
            dot.node(
                str(node.node_id),
                f"node_id={node.node_id}\nLabel: {node.value}\n Samples: {len(node.datapoints)}",
                shape="box",
            )

    else:
        # Add a decision node with feature and threshold
        dot.node(
            str(node.node_id),
            f"node_id={node.node_id}\n{feature_names[node.feature]} > {node.threshold}",
            shape="box",
        )

    # If there are children, add edges and recursively build the graph
    if node.lchild is not None:
        dot.edge(str(node.node_id), str(node.lchild.node_id), label="False")
        build_graph(dot, node.lchild, feature_names, depth + 1)

    if node.rchild is not None:
        dot.edge(str(node.node_id), str(node.rchild.node_id), label="True")
        build_graph(dot, node.rchild, feature_names, depth + 1)


def _find_leaf_node(x, node):
    """
    Traverses the tree to find the leaf node for a given data point 'x'.
    This function is fast as it only performs comparisons.
    """
    current_node = node
    while not current_node.is_leaf_node():
        if x[current_node.feature] <= current_node.threshold:
            current_node = current_node.lchild
        else:
            current_node = current_node.rchild
    return current_node


def predict_and_store(x, expected_label, weight, dist, node, feature_names):
    if node.is_leaf_node():
        data_point = pd.DataFrame(
            [np.append(x, [expected_label, weight, dist])],
            columns=list(feature_names) + ["label", "weight", "member"],
        )
        # node.datapoints = pd.concat([node.datapoints, data_point], ignore_index=True).drop_duplicates()
        node.datapoints = pd.concat([node.datapoints, data_point], ignore_index=True)
        # print(node.datapoints.shape, node.datapoints.columns)
        # print(node.datapoints.head())

        node.datapoints = node.datapoints.drop_duplicates(
            subset=[col for col in node.datapoints.columns if col != "weight"]
        )
        feature_cols = [
            col
            for col in node.datapoints.columns
            if col not in ("weight", "label", "member")
        ]
        grouped = node.datapoints.groupby(feature_cols)
        for key, group in grouped:
            if group["member"].nunique() > 1:
                print("Conflict detected for feature values:", key)
                print(group)
                raise ValueError(
                    "Conflict: Same datapoint with different 'member' values detected!"
                )

        node.value = most_common_label(node.datapoints["label"].values)
        return node.value
    if x[node.feature] <= node.threshold:
        return predict_and_store(
            x, expected_label, weight, dist, node.lchild, feature_names
        )
    else:
        return predict_and_store(
            x, expected_label, weight, dist, node.rchild, feature_names
        )


def most_common_label(y):
    counter = Counter(y)
    most_common = counter.most_common(1)[0][0]
    return most_common


def best_split(X, y, weights, num_features, used_features):
    best_gain = 0
    split_idx, split_threshold = None, None

    shuffled_feature_idx = list(range(num_features))
    random.shuffle(shuffled_feature_idx)

    for feature_idx in shuffled_feature_idx:
        if feature_idx in used_features:
            continue

        thresholds = np.unique(X[:, feature_idx])
        for threshold in thresholds:
            gain = information_gain(X, y, weights, feature_idx, threshold)
            if gain > best_gain:
                best_gain = gain
                split_idx = feature_idx
                split_threshold = threshold

    return split_idx, split_threshold


"""
def information_gain_old(X, y, weights, feature_idx, threshold):
    parent_entropy = entropy_old(y)
    left_indices = X[:, feature_idx] <= threshold
    right_indices = X[:, feature_idx] > threshold
    if len(left_indices) == 0 or len(right_indices) == 0:
        return 0

    n = len(y)
    n_left, n_right = len(y[left_indices]), len(y[right_indices])
    e_left, e_right = entropy_old(y[left_indices]), entropy_old(
        y[right_indices])
    child_entropy = (n_left / n) * e_left + (n_right / n) * e_right

    ig = parent_entropy - child_entropy
    return ig


def entropy_old(y):
    y = y.astype(int)
    hist = np.bincount(y)
    # print("Histogram :", hist)
    ps = hist / len(y)
    return -np.sum([p * np.log2(p) for p in ps if p > 0])
"""


def information_gain(X, y, weights, feature_idx, threshold):
    parent_entropy = entropy(y, weights)
    left_indices = X[:, feature_idx] <= threshold
    right_indices = X[:, feature_idx] > threshold
    if len(left_indices) == 0 or len(right_indices) == 0:
        return 0

    w = np.sum(weights)
    w_left, w_right = np.sum(weights[left_indices]), np.sum(weights[right_indices])
    e_left, e_right = entropy(y[left_indices], weights[left_indices]), entropy(
        y[right_indices], weights[right_indices]
    )
    child_entropy = (w_left / w) * e_left + (w_right / w) * e_right

    ig = parent_entropy - child_entropy
    return ig


def entropy(y, w):
    "Computes the weighted entropy of a set of binary labels."
    total_weight = np.sum(w)
    if total_weight == 0:
        return 0  # Avoid log(0)

    p1 = np.sum(w[y == 1]) / total_weight
    p0 = np.sum(w[y == 0]) / total_weight

    entropy = 0
    if p1 > 0:
        entropy -= p1 * np.log2(p1)
    if p0 > 0:
        entropy -= p0 * np.log2(p0)

    return entropy
