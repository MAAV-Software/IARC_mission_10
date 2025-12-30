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

// Compile command: g++ -g -O0 mapreduce/path_find.cpp -o mapreduce/path_find
// Execution command: ./mapreduce/path_find < output/grid-output.txt > output/path-output.txt

using namespace std;

/*
    // Quick binary search test to demonstrate the fundamentals behind binary search and how it works
    left = 1;
    right = 100;
    int number_to_guess = 84;
    int guess = 0;
    while(!(left > right)){
        mid = left + (right - left) / 2;
        cout << "The current guess is: " << guess << '\n';
        cout << "The left and right bounds are: " << left << " " << right << '\n';
        if(mid > number_to_guess){
            right = mid - 1;
        } 
        else{
            guess = mid;
            left = mid + 1;
        }
    }
    cout << "The number guessed is: " << guess << '\n';
*/

// Represents a node / point on the grid
struct Node{
    int i = 0;
    int j = 0;
};

// function to print out the grid
void print_grid(vector<vector<int>> grid, int path_width){
    for(int i = 0; i < grid.size(); ++i){
        for(int j = 0; j < grid[i].size(); ++j){
            cout << grid[i][j] << " ";
        }
        cout << '\n';
    }
}

vector<Node> get_square_of_radius(int radius, Node center_node, int height_bound, int width_bound){
    int center_i = center_node.i;
    int center_j = center_node.j;
    vector<Node> squircle_nodes;

    // get the top left corner of the squircle
    for(int i = 0; i <= radius; ++i){
        for(int j = 0; j <= radius; ++j){
            if((center_j - j >= 0) && (center_i - i >= 0)){
                Node node;
                node.i = center_i - i;
                node.j = center_j - j;
                squircle_nodes.push_back(node);
            }
        }
    }

    // get the bottom right corner of the squircle
    for(int i = 0; i <= radius; ++i){
        for(int j = 0; j <= radius; ++j){
            if((center_j + j < width_bound) && (center_i + i < height_bound)){
                Node node;
                node.i = center_i + i;
                node.j = center_j + j;
                squircle_nodes.push_back(node);
            }
        }
    }

    // get the bottom left corner of the squircle
    for(int i = 0; i <= radius; ++i){
        for(int j = 0; j <= radius; ++j){
            if((center_j - j >= 0) && (center_i + i < height_bound)){
                Node node;
                node.i = center_i + i;
                node.j = center_j - j;
                squircle_nodes.push_back(node);
            }
        }
    }

    // get the top right corner of the squircle
    for(int i = 0; i <= radius; ++i){
        for(int j = 0; j <= radius; ++j){
            if((center_j + j < width_bound) && (center_i - i >= 0)){
                Node node;
                node.i = center_i - i;
                node.j = center_j + j;
                squircle_nodes.push_back(node);
            }
        }
    }

    return squircle_nodes;

}

// read in the mine detections from the python mapreduce files
void read_in_grid(vector<vector<int>> &grid, int &rows, int &cols, double &footlong_width, double &footlong_height){
    vector<int> row;
    string temp;
    int num_cols = 0;
    int num_rows = 0;
    getline(cin, temp);
    stringstream ss(temp);
    ss >> footlong_width >> footlong_height;
    while(getline(cin, temp)){
        row.clear();
        int val = 0;
        ss.clear(); 
        ss.str(temp);
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

bool BFS_search(vector<vector<int>> grid, vector<vector<int>> explored_vals, vector<Node> &path, int path_width, vector<vector<int>> &final_grid){

    queue<pair<Node, vector<Node>>> search_nodes;
    vector<Node> temp_path;
    int height = grid.size();
    int width = grid[0].size();
    Node start_node;
    start_node.i = 0;
    start_node.j = width / 2;
    temp_path.push_back(start_node);
    search_nodes.push(make_pair(start_node, temp_path));
    bool path_found = false;

    while(!search_nodes.empty()){
        auto front = search_nodes.front();
        Node curr_search_node = front.first;
        vector<Node> path_to_node = front.second;
        search_nodes.pop();

        // Stopping condition, we already hit the other end of the field
        if(curr_search_node.i >= height - path_width && curr_search_node.i < height){
            bool stopping_condition = true;
            vector<Node> squircle_nodes = get_square_of_radius(path_width / 2, curr_search_node, height, width);
            for(int i = 0; i < squircle_nodes.size(); ++i){
                if(grid[squircle_nodes[i].i][squircle_nodes[i].j] == 1){
                    stopping_condition = false;
                    break;
                }
            }
            if(stopping_condition){
                path_to_node.push_back(curr_search_node);
                for(int i = 0; i < path_to_node.size(); ++i){
                    squircle_nodes = get_square_of_radius(path_width / 2, path_to_node[i], height, width);
                    grid[path_to_node[i].i][path_to_node[i].j] = 2;
                    for(int x = 0; x < squircle_nodes.size(); ++x){
                        grid[squircle_nodes[x].i][squircle_nodes[x].j] = 2;
                    }
                    // update the path, 2 represents the path on the grid
                }
                final_grid = grid;
                path_found = true; 
                break;
            }
        }

        // Search up right down and left nodes
        if(curr_search_node.i > path_width - 1){ // make sure we are not at the top row when we search the top
            Node up_node;
            up_node.i = curr_search_node.i - path_width;
            up_node.j = curr_search_node.j;
            if(!explored_vals[up_node.i][up_node.j]){
                explored_vals[up_node.i][up_node.j] = 1;
                vector<Node> squircle = get_square_of_radius(path_width / 2, up_node, height, width);
                int safe_to_move = true;
                for(int i = 0; i < squircle.size(); ++i){
                    if(grid[squircle[i].i][squircle[i].j] == 1){
                        safe_to_move = false;
                        break;
                    }
                }
                if(safe_to_move){
                    path_to_node.push_back(up_node);
                    search_nodes.push(make_pair(up_node, path_to_node));
                }
            }
        }

        if(curr_search_node.j <= width - path_width){
            Node up_node;
            up_node.i = curr_search_node.i;
            up_node.j = curr_search_node.j + path_width;
            if(!explored_vals[up_node.i][up_node.j]){
                explored_vals[up_node.i][up_node.j] = 1;
                vector<Node> squircle = get_square_of_radius(path_width / 2, up_node, height, width);
                int safe_to_move = true;
                for(int i = 0; i < squircle.size(); ++i){
                    if(grid[squircle[i].i][squircle[i].j] == 1){
                        safe_to_move = false;
                        break;
                    }
                }
                if(safe_to_move){
                    path_to_node.push_back(up_node);
                    search_nodes.push(make_pair(up_node, path_to_node));
                }
            }
        }

        if(curr_search_node.i <= height - path_width){
            Node up_node;
            up_node.i = curr_search_node.i + path_width;
            up_node.j = curr_search_node.j;
            if(!explored_vals[up_node.i][up_node.j]){
                explored_vals[up_node.i][up_node.j] = 1;
                vector<Node> squircle = get_square_of_radius(path_width / 2, up_node, height, width);
                int safe_to_move = true;
                for(int i = 0; i < squircle.size(); ++i){
                    if(grid[squircle[i].i][squircle[i].j] == 1){
                        safe_to_move = false;
                        break;
                    }
                }
                if(safe_to_move){
                    path_to_node.push_back(up_node);
                    search_nodes.push(make_pair(up_node, path_to_node));
                }
            }
        }

        if(curr_search_node.j > path_width - 1){
            Node up_node;
            up_node.i = curr_search_node.i;
            up_node.j = curr_search_node.j - path_width;
            if(!explored_vals[up_node.i][up_node.j]){
                explored_vals[up_node.i][up_node.j] = 1;
                vector<Node> squircle = get_square_of_radius(path_width / 2, up_node, height, width);
                int safe_to_move = true;
                for(int i = 0; i < squircle.size(); ++i){
                    if(grid[squircle[i].i][squircle[i].j] == 1){
                        safe_to_move = false;
                        break;
                    }
                }
                if(safe_to_move){
                    path_to_node.push_back(up_node);
                    search_nodes.push(make_pair(up_node, path_to_node));
                }
            }
        }
    }
    return path_found;
}

int main(){
    int rows = 0;
    int cols = 0;
    double footlong_width = 0;
    double footlong_height = 0;
    vector<vector<int>> grid(rows, vector<int>(cols));
    vector<vector<int>> explored_vals(rows, vector<int>(cols));
    read_in_grid(grid, rows, cols, footlong_width, footlong_height);
    explored_vals = grid;

    // Can run a binary search to find the widest possible path for this location of mines
    // Minimum is 1 pixel width, and max is width of the entire map

    int left = 1;
    int right = cols;
    bool path_found = false;
    int final_path_width = 1;
    vector<vector<int>> final_grid;
    vector<Node> path;

    // Use binary search to find a path of the largest width that can still find a path
    while(!(left > right)){
        int path_width = left + (right - left) / 2;
        path_found = BFS_search(grid, explored_vals, path, path_width, final_grid);
        if(!path_found){ // path is too wide, doesn't fit
            right = path_width - 1;
        }
        else{ // narrow enough, but there could be a wider path that we could use
            final_path_width = path_width;
            left = path_width + 1;
        }
    }

    // cout << "The final path width is: " << final_path_width << '\n';
    double path_width = final_path_width / footlong_width;
    double path_height = final_path_width / footlong_height;
    cout << path_width << " " << path_height << " \n";
    print_grid(final_grid, final_path_width);
}