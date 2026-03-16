/**
 * IARC Mission 10 - Enhanced Visualization Version
 * Saves circle radius and Voronoi edges for visualization
 */

#include <iostream>
#include <vector>
#include <cmath>
#include <random>
#include <chrono>
#include <queue>
#include <map>
#include <algorithm>
#include <fstream>
#include <iomanip>
#include <limits>

// CGAL includes for Voronoi
#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/Delaunay_triangulation_2.h>

typedef CGAL::Exact_predicates_inexact_constructions_kernel K;
typedef CGAL::Delaunay_triangulation_2<K> DT;
typedef K::Point_2 CGALPoint;

// Custom Point structure
struct Point {
    double x, y;
    
    Point(double x_ = 0, double y_ = 0) : x(x_), y(y_) {}
    
    double distance_to(const Point& other) const {
        double dx = x - other.x;
        double dy = y - other.y;
        return std::sqrt(dx * dx + dy * dy);
    }
    
    double distance_squared_to(const Point& other) const {
        double dx = x - other.x;
        double dy = y - other.y;
        return dx * dx + dy * dy;
    }
    
    Point operator-(const Point& other) const {
        return Point(x - other.x, y - other.y);
    }
    
    Point operator+(const Point& other) const {
        return Point(x + other.x, y + other.y);
    }
    
    Point operator*(double scalar) const {
        return Point(x * scalar, y * scalar);
    }
    
    double dot(const Point& other) const {
        return x * other.x + y * other.y;
    }
    
    bool operator==(const Point& other) const {
        return std::abs(x - other.x) < 1e-9 && std::abs(y - other.y) < 1e-9;
    }
    
    bool operator<(const Point& other) const {
        if (std::abs(x - other.x) > 1e-9) return x < other.x;
        return y < other.y;
    }
};

// Hash function for Point
struct PointHash {
    size_t operator()(const Point& p) const {
        return std::hash<double>()(p.x) ^ (std::hash<double>()(p.y) << 1);
    }
};

double distance_from_segment_to_point(const Point& seg_start, 
                                      const Point& seg_end,
                                      const Point& point) {
    Point v = seg_end - seg_start;
    Point w = point - seg_start;
    
    double segment_length_sq = v.dot(v);
    
    if (segment_length_sq < 1e-10) {
        return seg_start.distance_to(point);
    }
    
    double t = w.dot(v) / segment_length_sq;
    t = std::max(0.0, std::min(1.0, t));
    
    Point closest(seg_start.x + t * v.x, seg_start.y + t * v.y);
    
    return closest.distance_to(point);
}

/**
 * Base class for pathfinding methods
 */
class PathfinderBase {
protected:
    std::vector<Point> mines;
    Point start, end;
    double width, height;
    double mine_buffer;
    double mine_buffer_squared;
    std::vector<Point> path;
    double path_length;
    double computation_time_ms;
    
public:
    PathfinderBase(double width_, double height_, double buffer_)
        : width(width_), height(height_), mine_buffer(buffer_), 
          mine_buffer_squared(buffer_ * buffer_),
          path_length(0), computation_time_ms(0) {
        start = Point(0, height / 2);
        end = Point(width, height / 2);
    }
    
    void generate_minefield(int num_mines, unsigned seed = 42) {
        mines.clear();
        std::mt19937 gen(seed);
        std::uniform_real_distribution<> dist_x(10, width - 10);
        std::uniform_real_distribution<> dist_y(0, height);
        
        for (int i = 0; i < num_mines; ++i) {
            mines.push_back(Point(dist_x(gen), dist_y(gen)));
        }
    }
    
    bool is_point_safe(const Point& p) const {
        for (const auto& mine : mines) {
            if (p.distance_squared_to(mine) < mine_buffer_squared) {
                return false;
            }
        }
        return true;
    }
    
    bool is_edge_safe(const Point& p1, const Point& p2) const {
        for (const auto& mine : mines) {
            double dist = distance_from_segment_to_point(p1, p2, mine);
            if (dist < mine_buffer) {
                return false;
            }
        }
        return true;
    }
    
    double get_path_length() const { return path_length; }
    double get_computation_time() const { return computation_time_ms; }
    const std::vector<Point>& get_path() const { return path; }
    const std::vector<Point>& get_mines() const { return mines; }
    
    virtual bool find_path() = 0;
    virtual std::string get_method_name() const = 0;
};

/**
 * METHOD A: Tangent Circle Reduction Method with Visualization Data
 */
class TangentPathfinder : public PathfinderBase {
private:
    double successful_radius;  // Store the radius that worked
    
    struct Node {
        Point pos;
        double g_cost;
        double h_cost;
        double f_cost() const { return g_cost + h_cost; }
        
        bool operator>(const Node& other) const {
            return f_cost() > other.f_cost();
        }
    };
    
    std::vector<Point> find_tangent_points(const Point& p, const Point& center, double radius) {
        std::vector<Point> tangents;
        
        double dist = p.distance_to(center);
        if (dist <= radius) return tangents;
        
        double angle_to_center = std::atan2(center.y - p.y, center.x - p.x);
        double tangent_angle = std::asin(radius / dist);
        
        double angle1 = angle_to_center + tangent_angle;
        double angle2 = angle_to_center - tangent_angle;
        
        double tangent_dist = std::sqrt(dist * dist - radius * radius);
        
        tangents.push_back(Point(p.x + tangent_dist * std::cos(angle1), 
                                 p.y + tangent_dist * std::sin(angle1)));
        tangents.push_back(Point(p.x + tangent_dist * std::cos(angle2), 
                                 p.y + tangent_dist * std::sin(angle2)));
        
        return tangents;
    }
    
    std::vector<Point> get_waypoints_for_radius(double radius) {
        std::vector<Point> waypoints;
        waypoints.push_back(start);
        
        for (const auto& mine : mines) {
            auto tangents_from_start = find_tangent_points(start, mine, radius);
            waypoints.insert(waypoints.end(), tangents_from_start.begin(), tangents_from_start.end());
            
            auto tangents_from_end = find_tangent_points(end, mine, radius);
            waypoints.insert(waypoints.end(), tangents_from_end.begin(), tangents_from_end.end());
        }
        
        for (size_t i = 0; i < mines.size(); ++i) {
            for (size_t j = i + 1; j < mines.size(); ++j) {
                double dist = mines[i].distance_to(mines[j]);
                if (dist > 2 * radius) {
                    auto tangents = find_tangent_points(mines[i], mines[j], radius);
                    waypoints.insert(waypoints.end(), tangents.begin(), tangents.end());
                }
            }
        }
        
        waypoints.push_back(end);
        return waypoints;
    }
    
    bool a_star_search(const std::vector<Point>& waypoints, double radius) {
        std::priority_queue<Node, std::vector<Node>, std::greater<Node>> open_set;
        std::map<Point, double> g_score;
        std::map<Point, Point> came_from;
        
        Node start_node{start, 0, start.distance_to(end)};
        open_set.push(start_node);
        g_score[start] = 0;
        
        while (!open_set.empty()) {
            Node current = open_set.top();
            open_set.pop();
            
            if (current.pos == end) {
                path.clear();
                Point curr = end;
                while (!(curr == start)) {
                    path.push_back(curr);
                    curr = came_from[curr];
                }
                path.push_back(start);
                std::reverse(path.begin(), path.end());
                
                path_length = 0;
                for (size_t i = 1; i < path.size(); ++i) {
                    path_length += path[i-1].distance_to(path[i]);
                }
                return true;
            }
            
            for (const auto& neighbor : waypoints) {
                if (neighbor == current.pos) continue;
                
                bool safe = true;
                for (const auto& mine : mines) {
                    double dist = distance_from_segment_to_point(current.pos, neighbor, mine);
                    if (dist < radius - 0.01) {
                        safe = false;
                        break;
                    }
                }
                
                if (!safe) continue;
                
                double tentative_g = g_score[current.pos] + current.pos.distance_to(neighbor);
                
                if (g_score.find(neighbor) == g_score.end() || tentative_g < g_score[neighbor]) {
                    came_from[neighbor] = current.pos;
                    g_score[neighbor] = tentative_g;
                    Node neighbor_node{neighbor, tentative_g, neighbor.distance_to(end)};
                    open_set.push(neighbor_node);
                }
            }
        }
        
        return false;
    }
    
public:
    using PathfinderBase::PathfinderBase;
    
    bool find_path() override {
        auto start_time = std::chrono::high_resolution_clock::now();
        
        double max_radius = 15.0;
        double min_radius = mine_buffer;
        double radius_step = 0.5;
        
        bool found = false;
        successful_radius = -1;
        
        for (double radius = max_radius; radius >= min_radius; radius -= radius_step) {
            std::vector<Point> waypoints = get_waypoints_for_radius(radius);
            
            if (a_star_search(waypoints, radius)) {
                successful_radius = radius;  // Store the successful radius
                found = true;
                break;
            }
        }
        
        auto end_time = std::chrono::high_resolution_clock::now();
        computation_time_ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();
        
        return found;
    }
    
    std::string get_method_name() const override {
        return "Tangent Circle Reduction";
    }
    
    double get_successful_radius() const { return successful_radius; }
};

/**
 * METHOD B: Voronoi Diagram Method with Edge Storage
 */
class VoronoiPathfinder : public PathfinderBase {
public:
    struct Edge {
        Point p1, p2;
        double weight;
    };
    
private:
    std::vector<Edge> voronoi_edges;
    
    void build_voronoi_diagram() {
        DT dt;
        for (const auto& mine : mines) {
            dt.insert(CGALPoint(mine.x, mine.y));
        }
        
        voronoi_edges.clear();
        
        for (auto eit = dt.finite_edges_begin(); eit != dt.finite_edges_end(); ++eit) {
            auto f1 = eit->first;
            auto f2 = f1->neighbor(eit->second);
            
            if (!dt.is_infinite(f1) && !dt.is_infinite(f2)) {
                auto cc1 = dt.circumcenter(f1);
                auto cc2 = dt.circumcenter(f2);
                
                Point p1(cc1.x(), cc1.y());
                Point p2(cc2.x(), cc2.y());
                
                if (p1.x >= -50 && p1.x <= width + 50 && p1.y >= -50 && p1.y <= height + 50 &&
                    p2.x >= -50 && p2.x <= width + 50 && p2.y >= -50 && p2.y <= height + 50) {
                    
                    if (is_edge_safe(p1, p2)) {
                        Edge e{p1, p2, p1.distance_to(p2)};
                        voronoi_edges.push_back(e);
                    }
                }
            }
        }
        
        // Add boundary edges
        for (auto vit = dt.finite_vertices_begin(); vit != dt.finite_vertices_end(); ++vit) {
            auto vertex_point = vit->point();
            Point vp(vertex_point.x(), vertex_point.y());
            
            std::vector<Point> boundary_points;
            
            if (vp.x < width / 2) {
                Point bp(0, vp.y);
                if (is_edge_safe(vp, bp)) {
                    boundary_points.push_back(bp);
                }
            } else {
                Point bp(width, vp.y);
                if (is_edge_safe(vp, bp)) {
                    boundary_points.push_back(bp);
                }
            }
            
            if (vp.y < height / 2) {
                Point bp(vp.x, 0);
                if (is_edge_safe(vp, bp)) {
                    boundary_points.push_back(bp);
                }
            } else {
                Point bp(vp.x, height);
                if (is_edge_safe(vp, bp)) {
                    boundary_points.push_back(bp);
                }
            }
            
            for (const auto& bp : boundary_points) {
                Point midpoint((vp.x + bp.x) / 2, (vp.y + bp.y) / 2);
                if (is_point_safe(midpoint)) {
                    Edge e{midpoint, bp, midpoint.distance_to(bp)};
                    voronoi_edges.push_back(e);
                }
            }
        }
    }
    
    Point find_nearest_voronoi_point(const Point& p) {
        Point nearest = p;
        double min_dist = std::numeric_limits<double>::max();
        
        for (const auto& edge : voronoi_edges) {
            double d1 = p.distance_to(edge.p1);
            double d2 = p.distance_to(edge.p2);
            
            if (d1 < min_dist && is_edge_safe(p, edge.p1)) {
                min_dist = d1;
                nearest = edge.p1;
            }
            if (d2 < min_dist && is_edge_safe(p, edge.p2)) {
                min_dist = d2;
                nearest = edge.p2;
            }
        }
        
        return nearest;
    }
    
    bool dijkstra_search(const Point& start_voronoi, const Point& end_voronoi) {
        std::map<Point, std::vector<std::pair<Point, double>>> graph;
        
        for (const auto& edge : voronoi_edges) {
            graph[edge.p1].push_back({edge.p2, edge.weight});
            graph[edge.p2].push_back({edge.p1, edge.weight});
        }
        
        if (is_edge_safe(start, start_voronoi)) {
            graph[start].push_back({start_voronoi, start.distance_to(start_voronoi)});
            graph[start_voronoi].push_back({start, start.distance_to(start_voronoi)});
        }
        
        if (is_edge_safe(end_voronoi, end)) {
            graph[end_voronoi].push_back({end, end_voronoi.distance_to(end)});
            graph[end].push_back({end_voronoi, end_voronoi.distance_to(end)});
        }
        
        auto cmp = [](const std::pair<double, Point>& a, const std::pair<double, Point>& b) {
            if (std::abs(a.first - b.first) > 1e-9) return a.first > b.first;
            return a.second < b.second;
        };
        
        std::priority_queue<std::pair<double, Point>, 
                           std::vector<std::pair<double, Point>>,
                           decltype(cmp)> pq(cmp);
        
        std::map<Point, double> dist;
        std::map<Point, Point> parent;
        
        pq.push({0, start});
        dist[start] = 0;
        
        while (!pq.empty()) {
            auto [d, u] = pq.top();
            pq.pop();
            
            if (u == end) {
                path.clear();
                Point current = end;
                while (!(current == start)) {
                    path.push_back(current);
                    current = parent[current];
                }
                path.push_back(start);
                std::reverse(path.begin(), path.end());
                
                path_length = dist[end];
                return true;
            }
            
            if (d > dist[u]) continue;
            
            if (graph.find(u) != graph.end()) {
                for (const auto& [v, weight] : graph[u]) {
                    double new_dist = dist[u] + weight;
                    
                    if (dist.find(v) == dist.end() || new_dist < dist[v]) {
                        dist[v] = new_dist;
                        parent[v] = u;
                        pq.push({new_dist, v});
                    }
                }
            }
        }
        
        return false;
    }
    
public:
    using PathfinderBase::PathfinderBase;
    
    bool find_path() override {
        auto start_time = std::chrono::high_resolution_clock::now();
        
        build_voronoi_diagram();
        
        Point start_voronoi = find_nearest_voronoi_point(start);
        Point end_voronoi = find_nearest_voronoi_point(end);
        
        bool found = dijkstra_search(start_voronoi, end_voronoi);
        
        auto end_time = std::chrono::high_resolution_clock::now();
        computation_time_ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();
        
        return found;
    }
    
    std::string get_method_name() const override {
        return "Voronoi Diagram";
    }
    
    const std::vector<Edge>& get_voronoi_edges() const { return voronoi_edges; }
};

/**
 * Enhanced save function with visualization data
 */
void save_enhanced_results(const TangentPathfinder& tangent, const VoronoiPathfinder& voronoi,
                          const std::string& tangent_file, const std::string& voronoi_file) {
    // Save Tangent results with circle radius
    {
        std::ofstream file(tangent_file);
        
        file << "MINES\n";
        for (const auto& mine : tangent.get_mines()) {
            file << mine.x << "," << mine.y << "\n";
        }
        
        file << "PATH\n";
        for (const auto& point : tangent.get_path()) {
            file << point.x << "," << point.y << "\n";
        }
        
        file << "METRICS\n";
        file << "path_length," << tangent.get_path_length() << "\n";
        file << "computation_time_ms," << tangent.get_computation_time() << "\n";
        file << "successful_radius," << tangent.get_successful_radius() << "\n";
        
        file.close();
    }
    
    // Save Voronoi results with edges
    {
        std::ofstream file(voronoi_file);
        
        file << "MINES\n";
        for (const auto& mine : voronoi.get_mines()) {
            file << mine.x << "," << mine.y << "\n";
        }
        
        file << "PATH\n";
        for (const auto& point : voronoi.get_path()) {
            file << point.x << "," << point.y << "\n";
        }
        
        file << "VORONOI_EDGES\n";
        for (const auto& edge : voronoi.get_voronoi_edges()) {
            file << edge.p1.x << "," << edge.p1.y << "," 
                 << edge.p2.x << "," << edge.p2.y << "\n";
        }
        
        file << "METRICS\n";
        file << "path_length," << voronoi.get_path_length() << "\n";
        file << "computation_time_ms," << voronoi.get_computation_time() << "\n";
        
        file.close();
    }
}

double calculate_iarc_score(double path_length, double computation_time_s, 
                           double narrowest_width, int missed_mines, double weight_penalty) {
    double A = computation_time_s / 60.0;
    double B = missed_mines;
    double L = path_length;
    double W = narrowest_width;
    double N = weight_penalty;
    
    double score = (150000 * W) / ((1 + B) * L * (1 + 7*A + 100*N));
    return score;
}

int main() {
    std::cout << "================================================================================\n";
    std::cout << " IARC MISSION 10 - ENHANCED VISUALIZATION VERSION\n";
    std::cout << "================================================================================\n\n";
    
    const double ARENA_WIDTH = 300.0;
    const double ARENA_HEIGHT = 80.0;
    const double MINE_BUFFER = 3.0;
    const int NUM_MINES = 50;  // Use reasonable number
    
    std::cout << "Arena: " << ARENA_WIDTH << " x " << ARENA_HEIGHT << " feet\n";
    std::cout << "Mines: " << NUM_MINES << "\n";
    std::cout << "Safety buffer: " << MINE_BUFFER << " feet\n\n";
    
    TangentPathfinder tangent(ARENA_WIDTH, ARENA_HEIGHT, MINE_BUFFER);
    VoronoiPathfinder voronoi(ARENA_WIDTH, ARENA_HEIGHT, MINE_BUFFER);
    
    tangent.generate_minefield(NUM_MINES, 42);
    voronoi.generate_minefield(NUM_MINES, 42);
    
    std::cout << "------------------------------------------------------------\n";
    std::cout << "METHOD A: TANGENT CIRCLE REDUCTION\n";
    std::cout << "------------------------------------------------------------\n";
    
    bool tangent_found = tangent.find_path();
    if (tangent_found) {
        std::cout << "✓ Path found!\n";
        std::cout << "  Path length: " << std::fixed << std::setprecision(2) 
                  << tangent.get_path_length() << " feet\n";
        std::cout << "  Computation time: " << std::fixed << std::setprecision(2) 
                  << tangent.get_computation_time() << " ms\n";
        std::cout << "  Path points: " << tangent.get_path().size() << "\n";
        std::cout << "  Successful radius: " << std::fixed << std::setprecision(2) 
                  << tangent.get_successful_radius() << " feet\n";
        
        double tangent_score = calculate_iarc_score(
            tangent.get_path_length(),
            tangent.get_computation_time() / 1000.0,
            MINE_BUFFER, 0, 0
        );
        std::cout << "  IARC Score: " << std::fixed << std::setprecision(0) 
                  << tangent_score << "\n";
    } else {
        std::cout << "✗ No path found!\n";
    }
    
    std::cout << "\n------------------------------------------------------------\n";
    std::cout << "METHOD B: VORONOI DIAGRAM\n";
    std::cout << "------------------------------------------------------------\n";
    
    bool voronoi_found = voronoi.find_path();
    if (voronoi_found) {
        std::cout << "✓ Path found!\n";
        std::cout << "  Path length: " << std::fixed << std::setprecision(2) 
                  << voronoi.get_path_length() << " feet\n";
        std::cout << "  Computation time: " << std::fixed << std::setprecision(2) 
                  << voronoi.get_computation_time() << " ms\n";
        std::cout << "  Path points: " << voronoi.get_path().size() << "\n";
        std::cout << "  Voronoi edges: " << voronoi.get_voronoi_edges().size() << "\n";
        
        double voronoi_score = calculate_iarc_score(
            voronoi.get_path_length(),
            voronoi.get_computation_time() / 1000.0,
            MINE_BUFFER, 0, 0
        );
        std::cout << "  IARC Score: " << std::fixed << std::setprecision(0) 
                  << voronoi_score << "\n";
    } else {
        std::cout << "✗ No path found!\n";
    }
    
    // Save enhanced results
    save_enhanced_results(tangent, voronoi, "tangent_enhanced.txt", "voronoi_enhanced.txt");
    std::cout << "\n✓ Enhanced results saved for visualization!\n";
    
    return 0;
}
