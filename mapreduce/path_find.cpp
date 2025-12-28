#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <unordered_set>
#include <fstream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>
#include <random>
#include <chrono>

using namespace std;

struct Node{
    int i = 0;
    int j = 0;
};

void print_grid(vector<vector<int>> grid){
    for(int i = 0; i < grid.size(); ++i){
        for(int j = 0; j < grid[i].size(); ++j){
            cout << grid[i][j] << " ";
        }
        cout << '\n';
    }
}

void read_in_grid(vector<vector<int>> &grid, int &rows, int &cols){
    vector<int> row;
    string temp;
    int num_cols = 0;
    int num_rows = 0;
    while(getline(cin, temp)){
        row.clear();
        int val = 0;
        stringstream ss(temp);
        while(ss >> val){
            row.push_back(val);
        }
        grid.push_back(row);
        num_cols = row.size();
        num_rows++;
    }
    rows = num_rows;
    cols = num_cols;
}

int main(){
    int rows = 0;
    int cols = 0;
    vector<vector<int>> grid(rows, vector<int>(cols));
    vector<vector<int>> explored_vals(rows, vector<int>(cols));
    read_in_grid(grid, rows, cols);
    explored_vals = grid;

    queue<pair<Node, vector<Node>>> search_nodes;
    vector<Node> temp_path;
    Node start_node;
    start_node.i = rows - 1;
    start_node.j = 0;
    temp_path.push_back(start_node);
    search_nodes.push(make_pair(start_node, temp_path));

    int height = grid.size();
    int width = grid[0].size();

    while(!search_nodes.empty()){
        auto front = search_nodes.front();
        Node curr_search_node = front.first;
        vector<Node> path_to_node = front.second;
        search_nodes.pop();

        if(curr_search_node.i == 0){
            for(int i = 0; i < path_to_node.size(); ++i){
                grid[path_to_node[i].i][path_to_node[i].j] = 2;
            }  
            break;
        }
        
        // Search up right down and left nodes

        if(curr_search_node.i != 0){ // make sure we are not at the top row when we search the top
            if(!explored_vals[curr_search_node.i - 1][curr_search_node.j]){
                Node up_node;
                up_node.i = curr_search_node.i - 1;
                up_node.j = curr_search_node.j;
                explored_vals[curr_search_node.i - 1][curr_search_node.j] = true;
                path_to_node.push_back(up_node);
                search_nodes.push(make_pair(up_node, path_to_node));
            }
        }

        if(curr_search_node.j != width - 1){
            if(!explored_vals[curr_search_node.i][curr_search_node.j + 1]){
                Node up_node;
                up_node.i = curr_search_node.i;
                up_node.j = curr_search_node.j + 1;
                explored_vals[curr_search_node.i][curr_search_node.j + 1] = true;
                path_to_node.push_back(up_node);
                search_nodes.push(make_pair(up_node, path_to_node));
            }
        }

        if(curr_search_node.i != height - 1){
            if(!explored_vals[curr_search_node.i + 1][curr_search_node.j]){
                Node up_node;
                up_node.i = curr_search_node.i + 1;
                up_node.j = curr_search_node.j;
                explored_vals[curr_search_node.i + 1][curr_search_node.j] = true;
                path_to_node.push_back(up_node);
                search_nodes.push(make_pair(up_node, path_to_node));
            }
        }

        if(curr_search_node.j != 0){
            if(!explored_vals[curr_search_node.i][curr_search_node.j - 1]){
                Node up_node;
                up_node.i = curr_search_node.i;
                up_node.j = curr_search_node.j - 1;
                explored_vals[curr_search_node.i][curr_search_node.j - 1] = true;
                path_to_node.push_back(up_node);
                search_nodes.push(make_pair(up_node, path_to_node));
            }
        }
    }

    print_grid(grid);
}