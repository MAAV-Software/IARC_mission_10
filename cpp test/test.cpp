/**
 * IARC Mission 10 - Simple Test Version with Debug Output
 * Minimal implementation to test basic functionality
 */

#include <iostream>
#include <vector>
#include <cmath>
#include <chrono>
#include <algorithm>

struct Point {
    double x, y;
    
    Point(double x_ = 0, double y_ = 0) : x(x_), y(y_) {}
    
    double distance_to(const Point& other) const {
        double dx = x - other.x;
        double dy = y - other.y;
        return std::sqrt(dx * dx + dy * dy);
    }
};

double distance_from_segment_to_point(const Point& seg_start, 
                                      const Point& seg_end,
                                      const Point& point) {
    Point v(seg_end.x - seg_start.x, seg_end.y - seg_start.y);
    Point w(point.x - seg_start.x, point.y - seg_start.y);
    
    double segment_length_sq = v.x * v.x + v.y * v.y;
    
    if (segment_length_sq < 1e-10) {
        return seg_start.distance_to(point);
    }
    
    double t = (w.x * v.x + w.y * v.y) / segment_length_sq;
    t = std::max(0.0, std::min(1.0, t));
    
    Point closest(seg_start.x + t * v.x, seg_start.y + t * v.y);
    
    return closest.distance_to(point);
}

int main() {
    std::cout << "================================================================================\n";
    std::cout << " SIMPLE MINEFIELD TEST\n";
    std::cout << "================================================================================\n\n";
    
    const double ARENA_WIDTH = 300.0;
    const double ARENA_HEIGHT = 80.0;
    const double MINE_BUFFER = 3.0;
    
    // Test with just a few mines
    std::vector<Point> mines;
    mines.push_back(Point(150, 40));  // One mine in the middle
    
    Point start(0, 40);
    Point end(300, 40);
    
    std::cout << "Setup:\n";
    std::cout << "  Arena: " << ARENA_WIDTH << " x " << ARENA_HEIGHT << " feet\n";
    std::cout << "  Start: (" << start.x << ", " << start.y << ")\n";
    std::cout << "  End: (" << end.x << ", " << end.y << ")\n";
    std::cout << "  Mines: " << mines.size() << "\n";
    for (size_t i = 0; i < mines.size(); ++i) {
        std::cout << "    Mine " << i << ": (" << mines[i].x << ", " << mines[i].y << ")\n";
    }
    std::cout << "  Buffer: " << MINE_BUFFER << " feet\n\n";
    
    // Test 1: Direct path check
    std::cout << "Test 1: Checking direct path...\n";
    bool direct_safe = true;
    for (const auto& mine : mines) {
        double dist = distance_from_segment_to_point(start, end, mine);
        std::cout << "  Distance from direct path to mine: " << dist << " feet\n";
        if (dist < MINE_BUFFER) {
            std::cout << "  ✗ Direct path BLOCKED (too close to mine)\n";
            direct_safe = false;
        }
    }
    if (direct_safe) {
        std::cout << "  ✓ Direct path is SAFE!\n";
    }
    std::cout << "\n";
    
    // Test 2: Simple detour path
    std::cout << "Test 2: Testing simple detour paths...\n";
    
    // Go above the mine
    Point detour_up1(150, 40 + MINE_BUFFER + 1);  // Above mine
    std::cout << "  Path 1 (go above): Start -> (" << detour_up1.x << ", " << detour_up1.y << ") -> End\n";
    
    double dist1a = distance_from_segment_to_point(start, detour_up1, mines[0]);
    double dist1b = distance_from_segment_to_point(detour_up1, end, mines[0]);
    std::cout << "    Segment 1 distance to mine: " << dist1a << " feet\n";
    std::cout << "    Segment 2 distance to mine: " << dist1b << " feet\n";
    
    if (dist1a >= MINE_BUFFER && dist1b >= MINE_BUFFER) {
        double path_length = start.distance_to(detour_up1) + detour_up1.distance_to(end);
        std::cout << "    ✓ Path is SAFE! Total length: " << path_length << " feet\n";
    } else {
        std::cout << "    ✗ Path is BLOCKED\n";
    }
    
    // Go below the mine
    Point detour_down1(150, 40 - MINE_BUFFER - 1);  // Below mine
    std::cout << "  Path 2 (go below): Start -> (" << detour_down1.x << ", " << detour_down1.y << ") -> End\n";
    
    double dist2a = distance_from_segment_to_point(start, detour_down1, mines[0]);
    double dist2b = distance_from_segment_to_point(detour_down1, end, mines[0]);
    std::cout << "    Segment 1 distance to mine: " << dist2a << " feet\n";
    std::cout << "    Segment 2 distance to mine: " << dist2b << " feet\n";
    
    if (dist2a >= MINE_BUFFER && dist2b >= MINE_BUFFER) {
        double path_length = start.distance_to(detour_down1) + detour_down1.distance_to(end);
        std::cout << "    ✓ Path is SAFE! Total length: " << path_length << " feet\n";
    } else {
        std::cout << "    ✗ Path is BLOCKED\n";
    }
    
    std::cout << "\n";
    
    // Test 3: Timing test
    std::cout << "Test 3: Performance test...\n";
    auto start_time = std::chrono::high_resolution_clock::now();
    
    // Do some simple calculations
    int iterations = 1000000;
    double sum = 0;
    for (int i = 0; i < iterations; ++i) {
        sum += distance_from_segment_to_point(start, end, mines[0]);
    }
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    
    std::cout << "  Performed " << iterations << " distance calculations in " 
              << duration.count() << " ms\n";
    std::cout << "  Average: " << (double)duration.count() / iterations * 1000000 << " nanoseconds per calculation\n";
    
    std::cout << "\n✓ All tests complete!\n";
    
    return 0;
}