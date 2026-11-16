"""Catalogo de algoritmos prontos em Kotlin puro.

Cada algoritmo gera um arquivo em algorithms/ e um teste unitario correspondente.
"""

from collections import namedtuple

Algorithm = namedtuple("Algorithm", "key name category description cls code test")

ALGORITHMS_LIST = []


def algo(key, name, category, description, cls, code, test):
    ALGORITHMS_LIST.append(Algorithm(key, name, category, description, cls, code.strip("\n"), test.strip("\n")))


SORT = "Ordenacao"
SEARCH = "Busca"
GRAPH = "Grafos e rotas"
DP = "Programacao dinamica"
STR = "Texto"
MATH = "Matematica e estatistica"
FIN = "Financeiro"
DS = "Estruturas de dados"
UTIL = "Utilitarios"
VAL = "Validacao e seguranca"
ML = "Recomendacao e dados"

# ------------------------------------------------------------------ ordenacao
algo("bubble_sort", "Bubble Sort", SORT, "Ordenacao simples por trocas adjacentes, O(n^2).", "BubbleSort", r'''
/** Bubble sort com parada antecipada quando a lista ja esta ordenada. */
object BubbleSort {
    fun <T : Comparable<T>> sort(input: List<T>): List<T> {
        val items = input.toMutableList()
        for (i in 0 until items.size - 1) {
            var swapped = false
            for (j in 0 until items.size - 1 - i) {
                if (items[j] > items[j + 1]) {
                    val temp = items[j]
                    items[j] = items[j + 1]
                    items[j + 1] = temp
                    swapped = true
                }
            }
            if (!swapped) break
        }
        return items
    }
}
''', "assertEquals(listOf(1, 2, 3, 5), BubbleSort.sort(listOf(5, 2, 3, 1)))")

algo("insertion_sort", "Insertion Sort", SORT, "Eficiente para listas pequenas ou quase ordenadas.", "InsertionSort", r'''
/** Insertion sort estavel. */
object InsertionSort {
    fun <T : Comparable<T>> sort(input: List<T>): List<T> {
        val items = input.toMutableList()
        for (i in 1 until items.size) {
            val key = items[i]
            var j = i - 1
            while (j >= 0 && items[j] > key) {
                items[j + 1] = items[j]
                j--
            }
            items[j + 1] = key
        }
        return items
    }
}
''', "assertEquals(listOf(1, 2, 3, 4), InsertionSort.sort(listOf(4, 3, 2, 1)))")

algo("selection_sort", "Selection Sort", SORT, "Seleciona o menor elemento a cada passo.", "SelectionSort", r'''
/** Selection sort, O(n^2) com poucas trocas. */
object SelectionSort {
    fun <T : Comparable<T>> sort(input: List<T>): List<T> {
        val items = input.toMutableList()
        for (i in items.indices) {
            var min = i
            for (j in i + 1 until items.size) if (items[j] < items[min]) min = j
            if (min != i) {
                val temp = items[i]
                items[i] = items[min]
                items[min] = temp
            }
        }
        return items
    }
}
''', "assertEquals(listOf(-1, 0, 7), SelectionSort.sort(listOf(7, -1, 0)))")

algo("merge_sort", "Merge Sort", SORT, "Divisao e conquista, estavel, O(n log n).", "MergeSort", r'''
/** Merge sort recursivo e estavel. */
object MergeSort {
    fun <T : Comparable<T>> sort(items: List<T>): List<T> {
        if (items.size <= 1) return items
        val middle = items.size / 2
        return merge(sort(items.subList(0, middle)), sort(items.subList(middle, items.size)))
    }

    private fun <T : Comparable<T>> merge(left: List<T>, right: List<T>): List<T> {
        val result = ArrayList<T>(left.size + right.size)
        var i = 0
        var j = 0
        while (i < left.size && j < right.size) {
            if (left[i] <= right[j]) result.add(left[i++]) else result.add(right[j++])
        }
        while (i < left.size) result.add(left[i++])
        while (j < right.size) result.add(right[j++])
        return result
    }
}
''', "assertEquals(listOf(1, 2, 2, 9), MergeSort.sort(listOf(9, 2, 1, 2)))")

algo("quick_sort", "Quick Sort", SORT, "Ordenacao rapida in-place com pivo central, O(n log n) medio.", "QuickSort", r'''
/** Quick sort in-place (particao de Hoare). */
object QuickSort {
    fun <T : Comparable<T>> sort(input: List<T>): List<T> {
        val items = input.toMutableList()
        quick(items, 0, items.size - 1)
        return items
    }

    private fun <T : Comparable<T>> quick(items: MutableList<T>, low: Int, high: Int) {
        if (low >= high) return
        val pivot = items[(low + high) / 2]
        var i = low
        var j = high
        while (i <= j) {
            while (items[i] < pivot) i++
            while (items[j] > pivot) j--
            if (i <= j) {
                val temp = items[i]
                items[i] = items[j]
                items[j] = temp
                i++
                j--
            }
        }
        quick(items, low, j)
        quick(items, i, high)
    }
}
''', "assertEquals(listOf(1, 3, 4, 8, 9), QuickSort.sort(listOf(8, 3, 9, 1, 4)))")

algo("heap_sort", "Heap Sort", SORT, "Ordenacao com heap binario, O(n log n) garantido.", "HeapSort", r'''
/** Heap sort usando max-heap em array. */
object HeapSort {
    fun sort(input: IntArray): IntArray {
        val a = input.copyOf()
        val n = a.size
        for (i in n / 2 - 1 downTo 0) heapify(a, n, i)
        for (end in n - 1 downTo 1) {
            val temp = a[0]
            a[0] = a[end]
            a[end] = temp
            heapify(a, end, 0)
        }
        return a
    }

    private fun heapify(a: IntArray, size: Int, root: Int) {
        var largest = root
        val left = 2 * root + 1
        val right = 2 * root + 2
        if (left < size && a[left] > a[largest]) largest = left
        if (right < size && a[right] > a[largest]) largest = right
        if (largest != root) {
            val temp = a[root]
            a[root] = a[largest]
            a[largest] = temp
            heapify(a, size, largest)
        }
    }
}
''', "assertArrayEquals(intArrayOf(1, 2, 5, 7), HeapSort.sort(intArrayOf(7, 5, 2, 1)))")

algo("counting_sort", "Counting Sort", SORT, "Ordenacao linear para inteiros em intervalo pequeno.", "CountingSort", r'''
/** Counting sort para inteiros (aceita negativos). */
object CountingSort {
    fun sort(input: IntArray): IntArray {
        if (input.isEmpty()) return input
        val min = input.minOrNull()!!
        val max = input.maxOrNull()!!
        val counts = IntArray(max - min + 1)
        input.forEach { counts[it - min]++ }
        val result = IntArray(input.size)
        var index = 0
        counts.forEachIndexed { offset, count -> repeat(count) { result[index++] = offset + min } }
        return result
    }
}
''', "assertArrayEquals(intArrayOf(-2, 0, 3, 3), CountingSort.sort(intArrayOf(3, -2, 3, 0)))")

algo("radix_sort", "Radix Sort", SORT, "Ordenacao por digitos (LSD) para inteiros nao negativos.", "RadixSort", r'''
/** Radix sort LSD em base 10 para inteiros nao negativos. */
object RadixSort {
    fun sort(input: IntArray): IntArray {
        var a = input.copyOf()
        val max = a.maxOrNull() ?: return a
        var exp = 1
        while (max / exp > 0) {
            val output = IntArray(a.size)
            val count = IntArray(10)
            a.forEach { count[(it / exp) % 10]++ }
            for (i in 1 until 10) count[i] += count[i - 1]
            for (i in a.indices.reversed()) {
                val digit = (a[i] / exp) % 10
                output[--count[digit]] = a[i]
            }
            a = output
            exp *= 10
        }
        return a
    }
}
''', "assertArrayEquals(intArrayOf(2, 24, 45, 170), RadixSort.sort(intArrayOf(170, 45, 2, 24)))")

# ------------------------------------------------------------------ busca
algo("binary_search", "Busca binaria", SEARCH, "Encontra um valor em lista ordenada, O(log n).", "BinarySearch", r'''
/** Busca binaria iterativa. Retorna o indice ou -1. */
object BinarySearch {
    fun <T : Comparable<T>> search(sorted: List<T>, target: T): Int {
        var low = 0
        var high = sorted.size - 1
        while (low <= high) {
            val middle = (low + high) ushr 1
            val comparison = sorted[middle].compareTo(target)
            when {
                comparison == 0 -> return middle
                comparison < 0 -> low = middle + 1
                else -> high = middle - 1
            }
        }
        return -1
    }

    /** Primeiro indice cujo valor e >= target (lower bound). */
    fun <T : Comparable<T>> lowerBound(sorted: List<T>, target: T): Int {
        var low = 0
        var high = sorted.size
        while (low < high) {
            val middle = (low + high) ushr 1
            if (sorted[middle] < target) low = middle + 1 else high = middle
        }
        return low
    }
}
''', "assertEquals(2, BinarySearch.search(listOf(1, 3, 5, 7), 5))\n        assertEquals(-1, BinarySearch.search(listOf(1, 3), 2))")

algo("linear_search", "Busca linear com filtro", SEARCH, "Busca sequencial com predicado.", "LinearSearch", r'''
/** Busca sequencial generica. */
object LinearSearch {
    fun <T> indexOfFirst(items: List<T>, predicate: (T) -> Boolean): Int {
        for (i in items.indices) if (predicate(items[i])) return i
        return -1
    }
}
''', "assertEquals(1, LinearSearch.indexOfFirst(listOf(\"a\", \"b\")) { it == \"b\" })")

algo("autocomplete_trie", "Autocompletar (Trie)", SEARCH, "Sugestoes por prefixo com arvore Trie.", "Trie", r'''
/** Arvore de prefixos para autocompletar. */
class Trie {
    private class Node {
        val children = HashMap<Char, Node>()
        var isWord = false
    }

    private val root = Node()

    fun insert(word: String) {
        var node = root
        word.lowercase().forEach { node = node.children.getOrPut(it) { Node() } }
        node.isWord = true
    }

    fun contains(word: String): Boolean {
        var node = root
        word.lowercase().forEach { node = node.children[it] ?: return false }
        return node.isWord
    }

    /** Retorna ate [limit] palavras que comecam com [prefix]. */
    fun suggestions(prefix: String, limit: Int = 10): List<String> {
        var node = root
        val lower = prefix.lowercase()
        lower.forEach { node = node.children[it] ?: return emptyList() }
        val result = mutableListOf<String>()
        fun walk(current: Node, path: StringBuilder) {
            if (result.size >= limit) return
            if (current.isWord) result.add(path.toString())
            current.children.toSortedMap().forEach { (char, child) ->
                path.append(char)
                walk(child, path)
                path.deleteCharAt(path.length - 1)
            }
        }
        walk(node, StringBuilder(lower))
        return result
    }
}
''', "val trie = Trie()\n        listOf(\"casa\", \"carro\", \"bola\").forEach { trie.insert(it) }\n        assertEquals(listOf(\"carro\", \"casa\"), trie.suggestions(\"ca\"))")

# ------------------------------------------------------------------ grafos
algo("bfs", "Busca em largura (BFS)", GRAPH, "Caminho com menor numero de passos em grafo nao ponderado.", "BreadthFirstSearch", r'''
/** BFS em grafo representado por lista de adjacencia. */
object BreadthFirstSearch {
    fun <T> shortestPath(graph: Map<T, List<T>>, start: T, goal: T): List<T> {
        val previous = HashMap<T, T>()
        val visited = hashSetOf(start)
        val queue = ArrayDeque(listOf(start))
        while (queue.isNotEmpty()) {
            val node = queue.removeFirst()
            if (node == goal) break
            for (next in graph[node].orEmpty()) {
                if (visited.add(next)) {
                    previous[next] = node
                    queue.addLast(next)
                }
            }
        }
        if (start != goal && goal !in previous) return emptyList()
        val path = mutableListOf(goal)
        while (path.last() != start) path.add(previous.getValue(path.last()))
        return path.reversed()
    }
}
''', "val g = mapOf(1 to listOf(2, 3), 2 to listOf(4), 3 to listOf(4))\n        assertEquals(listOf(1, 2, 4), BreadthFirstSearch.shortestPath(g, 1, 4))")

algo("dfs", "Busca em profundidade (DFS)", GRAPH, "Percorre todos os nos alcancaveis.", "DepthFirstSearch", r'''
/** DFS iterativa que retorna a ordem de visita. */
object DepthFirstSearch {
    fun <T> traverse(graph: Map<T, List<T>>, start: T): List<T> {
        val visited = LinkedHashSet<T>()
        val stack = ArrayDeque(listOf(start))
        while (stack.isNotEmpty()) {
            val node = stack.removeLast()
            if (!visited.add(node)) continue
            graph[node].orEmpty().reversed().forEach { if (it !in visited) stack.addLast(it) }
        }
        return visited.toList()
    }
}
''', "assertEquals(listOf(1, 2, 3), DepthFirstSearch.traverse(mapOf(1 to listOf(2, 3)), 1))")

algo("dijkstra", "Dijkstra (menor caminho)", GRAPH, "Menor caminho em grafo com pesos positivos (rotas, entregas).", "Dijkstra", r'''
import java.util.PriorityQueue

/** Algoritmo de Dijkstra com fila de prioridade. */
object Dijkstra {
    data class Edge<T>(val to: T, val weight: Double)

    /** Retorna o custo total e o caminho, ou null se nao houver caminho. */
    fun <T> shortestPath(graph: Map<T, List<Edge<T>>>, start: T, goal: T): Pair<Double, List<T>>? {
        val distance = HashMap<T, Double>().apply { put(start, 0.0) }
        val previous = HashMap<T, T>()
        val queue = PriorityQueue<Pair<T, Double>>(compareBy { it.second })
        queue.add(start to 0.0)
        while (queue.isNotEmpty()) {
            val (node, cost) = queue.poll()!!
            if (node == goal) break
            if (cost > (distance[node] ?: Double.MAX_VALUE)) continue
            for (edge in graph[node].orEmpty()) {
                val candidate = cost + edge.weight
                if (candidate < (distance[edge.to] ?: Double.MAX_VALUE)) {
                    distance[edge.to] = candidate
                    previous[edge.to] = node
                    queue.add(edge.to to candidate)
                }
            }
        }
        val total = distance[goal] ?: return null
        val path = mutableListOf(goal)
        while (path.last() != start) path.add(previous.getValue(path.last()))
        return total to path.reversed()
    }
}
''', "val g = mapOf(\"A\" to listOf(Dijkstra.Edge(\"B\", 1.0), Dijkstra.Edge(\"C\", 4.0)), \"B\" to listOf(Dijkstra.Edge(\"C\", 1.0)))\n        assertEquals(2.0, Dijkstra.shortestPath(g, \"A\", \"C\")!!.first, 0.001)")

algo("a_star", "A* em grade", GRAPH, "Caminho em mapas de grade com obstaculos (jogos, plantas).", "AStarGrid", r'''
import java.util.PriorityQueue
import kotlin.math.abs

/** A* em grade 2D. true = celula livre. Movimento em 4 direcoes. */
object AStarGrid {
    data class Cell(val row: Int, val col: Int)

    fun findPath(grid: Array<BooleanArray>, start: Cell, goal: Cell): List<Cell> {
        fun h(c: Cell) = abs(c.row - goal.row) + abs(c.col - goal.col)
        val g = HashMap<Cell, Int>().apply { put(start, 0) }
        val previous = HashMap<Cell, Cell>()
        val open = PriorityQueue<Pair<Cell, Int>>(compareBy { it.second })
        open.add(start to h(start))
        val directions = listOf(1 to 0, -1 to 0, 0 to 1, 0 to -1)
        while (open.isNotEmpty()) {
            val current = open.poll()!!.first
            if (current == goal) {
                val path = mutableListOf(goal)
                while (path.last() != start) path.add(previous.getValue(path.last()))
                return path.reversed()
            }
            for ((dr, dc) in directions) {
                val next = Cell(current.row + dr, current.col + dc)
                if (next.row !in grid.indices || next.col !in grid[0].indices || !grid[next.row][next.col]) continue
                val cost = g.getValue(current) + 1
                if (cost < (g[next] ?: Int.MAX_VALUE)) {
                    g[next] = cost
                    previous[next] = current
                    open.add(next to cost + h(next))
                }
            }
        }
        return emptyList()
    }
}
''', "val grid = Array(3) { BooleanArray(3) { true } }\n        assertEquals(5, AStarGrid.findPath(grid, AStarGrid.Cell(0, 0), AStarGrid.Cell(2, 2)).size)")

algo("topological_sort", "Ordenacao topologica", GRAPH, "Ordem de tarefas com dependencias (Kahn).", "TopologicalSort", r'''
/** Algoritmo de Kahn. Retorna null se houver ciclo. */
object TopologicalSort {
    fun <T> sort(dependencies: Map<T, List<T>>): List<T>? {
        val nodes = (dependencies.keys + dependencies.values.flatten()).toSet()
        val inDegree = nodes.associateWith { 0 }.toMutableMap()
        dependencies.values.flatten().forEach { inDegree[it] = inDegree.getValue(it) + 1 }
        val queue = ArrayDeque(nodes.filter { inDegree[it] == 0 })
        val result = mutableListOf<T>()
        while (queue.isNotEmpty()) {
            val node = queue.removeFirst()
            result.add(node)
            dependencies[node].orEmpty().forEach {
                inDegree[it] = inDegree.getValue(it) - 1
                if (inDegree[it] == 0) queue.addLast(it)
            }
        }
        return if (result.size == nodes.size) result else null
    }
}
''', "assertEquals(listOf(\"a\", \"b\", \"c\"), TopologicalSort.sort(mapOf(\"a\" to listOf(\"b\"), \"b\" to listOf(\"c\"))))")

algo("union_find", "Union-Find", GRAPH, "Conjuntos disjuntos com compressao de caminho.", "UnionFind", r'''
/** Estrutura Union-Find (Disjoint Set Union). */
class UnionFind(size: Int) {
    private val parent = IntArray(size) { it }
    private val rank = IntArray(size)

    fun find(x: Int): Int {
        if (parent[x] != x) parent[x] = find(parent[x])
        return parent[x]
    }

    fun union(a: Int, b: Int): Boolean {
        val rootA = find(a)
        val rootB = find(b)
        if (rootA == rootB) return false
        when {
            rank[rootA] < rank[rootB] -> parent[rootA] = rootB
            rank[rootA] > rank[rootB] -> parent[rootB] = rootA
            else -> {
                parent[rootB] = rootA
                rank[rootA]++
            }
        }
        return true
    }

    fun connected(a: Int, b: Int) = find(a) == find(b)
}
''', "val uf = UnionFind(4)\n        uf.union(0, 1)\n        assertTrue(uf.connected(0, 1))\n        assertFalse(uf.connected(0, 2))")

algo("kruskal", "Arvore geradora minima (Kruskal)", GRAPH, "Conecta pontos com o menor custo total (redes, cabos).", "Kruskal", r'''
/** Kruskal para arvore geradora minima. Vertices numerados de 0 a n-1. */
object Kruskal {
    data class Edge(val from: Int, val to: Int, val weight: Double)

    fun minimumSpanningTree(vertexCount: Int, edges: List<Edge>): List<Edge> {
        val parent = IntArray(vertexCount) { it }
        fun find(x: Int): Int {
            var node = x
            while (parent[node] != node) {
                parent[node] = parent[parent[node]]
                node = parent[node]
            }
            return node
        }
        val result = mutableListOf<Edge>()
        for (edge in edges.sortedBy { it.weight }) {
            val a = find(edge.from)
            val b = find(edge.to)
            if (a != b) {
                parent[a] = b
                result.add(edge)
            }
        }
        return result
    }
}
''', "val mst = Kruskal.minimumSpanningTree(3, listOf(Kruskal.Edge(0, 1, 1.0), Kruskal.Edge(1, 2, 2.0), Kruskal.Edge(0, 2, 5.0)))\n        assertEquals(3.0, mst.sumOf { it.weight }, 0.001)")

algo("floyd_warshall", "Floyd-Warshall", GRAPH, "Menores distancias entre todos os pares de vertices.", "FloydWarshall", r'''
/** Distancias minimas entre todos os pares. Use Double.POSITIVE_INFINITY para ausencia de aresta. */
object FloydWarshall {
    fun distances(matrix: Array<DoubleArray>): Array<DoubleArray> {
        val n = matrix.size
        val d = Array(n) { matrix[it].copyOf() }
        for (k in 0 until n) for (i in 0 until n) for (j in 0 until n) {
            if (d[i][k] + d[k][j] < d[i][j]) d[i][j] = d[i][k] + d[k][j]
        }
        return d
    }
}
''', "val inf = Double.POSITIVE_INFINITY\n        val d = FloydWarshall.distances(arrayOf(doubleArrayOf(0.0, 1.0, inf), doubleArrayOf(inf, 0.0, 2.0), doubleArrayOf(inf, inf, 0.0)))\n        assertEquals(3.0, d[0][2], 0.001)")

algo("tsp_nearest", "Rota de entregas (vizinho mais proximo)", GRAPH, "Ordem aproximada para visitar varios pontos geograficos.", "DeliveryRoute", r'''
/** Heuristica do vizinho mais proximo para ordenar paradas de entrega. */
object DeliveryRoute {
    data class Stop(val name: String, val latitude: Double, val longitude: Double)

    fun order(start: Stop, stops: List<Stop>): List<Stop> {
        val remaining = stops.toMutableList()
        val route = mutableListOf(start)
        while (remaining.isNotEmpty()) {
            val last = route.last()
            val next = remaining.minByOrNull { Haversine.distanceKm(last.latitude, last.longitude, it.latitude, it.longitude) }!!
            route.add(next)
            remaining.remove(next)
        }
        return route
    }
}
''', "val s = DeliveryRoute.Stop(\"base\", 0.0, 0.0)\n        val r = DeliveryRoute.order(s, listOf(DeliveryRoute.Stop(\"longe\", 5.0, 5.0), DeliveryRoute.Stop(\"perto\", 1.0, 1.0)))\n        assertEquals(\"perto\", r[1].name)")

# ------------------------------------------------------------------ programacao dinamica
algo("fibonacci", "Fibonacci (memoizado)", DP, "Sequencia de Fibonacci em tempo linear.", "Fibonacci", r'''
/** Fibonacci iterativo em O(n). */
object Fibonacci {
    fun nth(n: Int): Long {
        require(n >= 0)
        var a = 0L
        var b = 1L
        repeat(n) {
            val next = a + b
            a = b
            b = next
        }
        return a
    }
}
''', "assertEquals(55L, Fibonacci.nth(10))")

algo("knapsack", "Mochila 0/1", DP, "Escolhe itens que maximizam valor dentro de uma capacidade.", "Knapsack", r'''
/** Problema da mochila 0/1. Retorna o valor maximo e os indices escolhidos. */
object Knapsack {
    fun solve(weights: IntArray, values: IntArray, capacity: Int): Pair<Int, List<Int>> {
        val n = weights.size
        val dp = Array(n + 1) { IntArray(capacity + 1) }
        for (i in 1..n) for (w in 0..capacity) {
            dp[i][w] = dp[i - 1][w]
            if (weights[i - 1] <= w) dp[i][w] = maxOf(dp[i][w], dp[i - 1][w - weights[i - 1]] + values[i - 1])
        }
        val chosen = mutableListOf<Int>()
        var w = capacity
        for (i in n downTo 1) {
            if (dp[i][w] != dp[i - 1][w]) {
                chosen.add(i - 1)
                w -= weights[i - 1]
            }
        }
        return dp[n][capacity] to chosen.reversed()
    }
}
''', "assertEquals(9, Knapsack.solve(intArrayOf(1, 3, 4), intArrayOf(1, 4, 5), 7).first)")

algo("lcs", "Maior subsequencia comum (LCS)", DP, "Compara textos (diff simples).", "LongestCommonSubsequence", r'''
/** Maior subsequencia comum entre duas strings. */
object LongestCommonSubsequence {
    fun find(a: String, b: String): String {
        val dp = Array(a.length + 1) { IntArray(b.length + 1) }
        for (i in 1..a.length) for (j in 1..b.length) {
            dp[i][j] = if (a[i - 1] == b[j - 1]) dp[i - 1][j - 1] + 1 else maxOf(dp[i - 1][j], dp[i][j - 1])
        }
        val result = StringBuilder()
        var i = a.length
        var j = b.length
        while (i > 0 && j > 0) {
            when {
                a[i - 1] == b[j - 1] -> {
                    result.append(a[i - 1])
                    i--
                    j--
                }
                dp[i - 1][j] >= dp[i][j - 1] -> i--
                else -> j--
            }
        }
        return result.reverse().toString()
    }
}
''', "assertEquals(4, LongestCommonSubsequence.find(\"ABCBDAB\", \"BDCABA\").length)")

algo("levenshtein", "Distancia de edicao (Levenshtein)", DP, "Mede semelhanca entre textos (corretor, busca tolerante).", "Levenshtein", r'''
/** Distancia de Levenshtein e similaridade de 0 a 1. */
object Levenshtein {
    fun distance(a: String, b: String): Int {
        val previous = IntArray(b.length + 1) { it }
        val current = IntArray(b.length + 1)
        for (i in 1..a.length) {
            current[0] = i
            for (j in 1..b.length) {
                val cost = if (a[i - 1] == b[j - 1]) 0 else 1
                current[j] = minOf(current[j - 1] + 1, previous[j] + 1, previous[j - 1] + cost)
            }
            current.copyInto(previous)
        }
        return previous[b.length]
    }

    fun similarity(a: String, b: String): Double {
        val longest = maxOf(a.length, b.length)
        return if (longest == 0) 1.0 else 1.0 - distance(a, b).toDouble() / longest
    }
}
''', "assertEquals(3, Levenshtein.distance(\"kitten\", \"sitting\"))")

algo("lis", "Maior subsequencia crescente", DP, "Tendencias de alta em series (O(n log n)).", "LongestIncreasingSubsequence", r'''
/** Comprimento da maior subsequencia estritamente crescente. */
object LongestIncreasingSubsequence {
    fun length(values: IntArray): Int {
        val tails = mutableListOf<Int>()
        for (value in values) {
            var low = 0
            var high = tails.size
            while (low < high) {
                val middle = (low + high) / 2
                if (tails[middle] < value) low = middle + 1 else high = middle
            }
            if (low == tails.size) tails.add(value) else tails[low] = value
        }
        return tails.size
    }
}
''', "assertEquals(4, LongestIncreasingSubsequence.length(intArrayOf(10, 9, 2, 5, 3, 7, 101, 18)))")

algo("coin_change", "Troco minimo", DP, "Menor numero de moedas/notas para um valor (PDV, caixa).", "CoinChange", r'''
/** Calcula o menor numero de moedas e a composicao do troco (valores em centavos). */
object CoinChange {
    fun minCoins(coins: IntArray, amount: Int): List<Int>? {
        val dp = IntArray(amount + 1) { Int.MAX_VALUE }
        val last = IntArray(amount + 1) { -1 }
        dp[0] = 0
        for (value in 1..amount) for (coin in coins) {
            if (coin <= value && dp[value - coin] != Int.MAX_VALUE && dp[value - coin] + 1 < dp[value]) {
                dp[value] = dp[value - coin] + 1
                last[value] = coin
            }
        }
        if (dp[amount] == Int.MAX_VALUE) return null
        val result = mutableListOf<Int>()
        var remaining = amount
        while (remaining > 0) {
            result.add(last[remaining])
            remaining -= last[remaining]
        }
        return result.sortedDescending()
    }
}
''', "assertEquals(listOf(25, 25, 10), CoinChange.minCoins(intArrayOf(1, 5, 10, 25), 60))")

# ------------------------------------------------------------------ texto
algo("kmp", "Busca de padrao (KMP)", STR, "Encontra todas as ocorrencias de um padrao em O(n + m).", "KmpSearch", r'''
/** Knuth-Morris-Pratt. Retorna os indices de inicio de cada ocorrencia. */
object KmpSearch {
    fun findAll(text: String, pattern: String): List<Int> {
        if (pattern.isEmpty()) return emptyList()
        val lps = IntArray(pattern.length)
        var length = 0
        for (i in 1 until pattern.length) {
            while (length > 0 && pattern[i] != pattern[length]) length = lps[length - 1]
            if (pattern[i] == pattern[length]) length++
            lps[i] = length
        }
        val result = mutableListOf<Int>()
        var j = 0
        for (i in text.indices) {
            while (j > 0 && text[i] != pattern[j]) j = lps[j - 1]
            if (text[i] == pattern[j]) j++
            if (j == pattern.length) {
                result.add(i - j + 1)
                j = lps[j - 1]
            }
        }
        return result
    }
}
''', "assertEquals(listOf(0, 2), KmpSearch.findAll(\"ababa\", \"aba\"))")

algo("text_utils", "Utilitarios de texto", STR, "Remover acentos, slug, palindromo, anagrama, iniciais e capitalizacao.", "TextUtils", r'''
import java.text.Normalizer

/** Funcoes comuns de manipulacao de texto. */
object TextUtils {
    fun removeAccents(text: String): String =
        Normalizer.normalize(text, Normalizer.Form.NFD).replace(Regex("\\p{Mn}+"), "")

    fun slugify(text: String): String =
        removeAccents(text).lowercase().replace(Regex("[^a-z0-9]+"), "-").trim('-')

    fun isPalindrome(text: String): Boolean {
        val clean = removeAccents(text).lowercase().filter { it.isLetterOrDigit() }
        return clean == clean.reversed()
    }

    fun isAnagram(a: String, b: String): Boolean {
        fun key(s: String) = removeAccents(s).lowercase().filter { it.isLetter() }.toList().sorted()
        return key(a) == key(b)
    }

    fun initials(name: String, max: Int = 2): String =
        name.split(" ").filter { it.isNotBlank() }.take(max).joinToString("") { it.first().uppercase() }

    fun capitalizeWords(text: String): String =
        text.lowercase().split(" ").joinToString(" ") { word -> word.replaceFirstChar { it.uppercase() } }

    fun truncate(text: String, max: Int): String = if (text.length <= max) text else text.take(max - 3) + "..."

    fun wordFrequency(text: String): Map<String, Int> =
        removeAccents(text).lowercase().split(Regex("[^a-z0-9]+")).filter { it.isNotBlank() }
            .groupingBy { it }.eachCount().toList().sortedByDescending { it.second }.toMap()
}
''', "assertEquals(\"ola-mundo\", TextUtils.slugify(\"Olá, Mundo!\"))\n        assertTrue(TextUtils.isPalindrome(\"Ame a ema\"))")

algo("roman_numerals", "Numeros romanos", STR, "Converte inteiros para algarismos romanos e vice-versa.", "RomanNumerals", r'''
/** Conversao entre inteiros (1 a 3999) e numeros romanos. */
object RomanNumerals {
    private val table = listOf(
        1000 to "M", 900 to "CM", 500 to "D", 400 to "CD", 100 to "C", 90 to "XC",
        50 to "L", 40 to "XL", 10 to "X", 9 to "IX", 5 to "V", 4 to "IV", 1 to "I"
    )

    fun toRoman(number: Int): String {
        require(number in 1..3999)
        var remaining = number
        val builder = StringBuilder()
        for ((value, symbol) in table) {
            while (remaining >= value) {
                builder.append(symbol)
                remaining -= value
            }
        }
        return builder.toString()
    }

    fun fromRoman(roman: String): Int {
        val values = mapOf('I' to 1, 'V' to 5, 'X' to 10, 'L' to 50, 'C' to 100, 'D' to 500, 'M' to 1000)
        var total = 0
        for (i in roman.indices) {
            val current = values.getValue(roman[i])
            val next = if (i + 1 < roman.length) values.getValue(roman[i + 1]) else 0
            total += if (current < next) -current else current
        }
        return total
    }
}
''', "assertEquals(\"MCMXCIV\", RomanNumerals.toRoman(1994))\n        assertEquals(1994, RomanNumerals.fromRoman(\"MCMXCIV\"))")

algo("number_base", "Conversao de bases", STR, "Binario, octal, hexadecimal e base arbitraria.", "BaseConverter", r'''
/** Conversoes entre bases numericas de 2 a 36. */
object BaseConverter {
    fun convert(value: String, fromBase: Int, toBase: Int): String =
        value.trim().toLong(fromBase).toString(toBase).uppercase()

    fun toBinary(value: Long): String = value.toString(2)

    fun toHex(value: Long): String = value.toString(16).uppercase()
}
''', "assertEquals(\"FF\", BaseConverter.convert(\"255\", 10, 16))")

# ------------------------------------------------------------------ matematica
algo("gcd_lcm", "MDC e MMC", MATH, "Maximo divisor comum e minimo multiplo comum.", "GcdLcm", r'''
/** MDC pelo algoritmo de Euclides e MMC. */
object GcdLcm {
    tailrec fun gcd(a: Long, b: Long): Long = if (b == 0L) kotlin.math.abs(a) else gcd(b, a % b)

    fun lcm(a: Long, b: Long): Long = if (a == 0L || b == 0L) 0L else kotlin.math.abs(a / gcd(a, b) * b)
}
''', "assertEquals(6L, GcdLcm.gcd(54, 24))\n        assertEquals(36L, GcdLcm.lcm(12, 18))")

algo("primes", "Numeros primos (Crivo)", MATH, "Crivo de Eratostenes e teste de primalidade.", "Primes", r'''
/** Geracao e teste de numeros primos. */
object Primes {
    fun sieve(limit: Int): List<Int> {
        if (limit < 2) return emptyList()
        val composite = BooleanArray(limit + 1)
        var i = 2
        while (i.toLong() * i <= limit) {
            if (!composite[i]) {
                var j = i * i
                while (j <= limit) {
                    composite[j] = true
                    j += i
                }
            }
            i++
        }
        return (2..limit).filter { !composite[it] }
    }

    fun isPrime(n: Long): Boolean {
        if (n < 2) return false
        if (n < 4) return true
        if (n % 2 == 0L || n % 3 == 0L) return false
        var i = 5L
        while (i * i <= n) {
            if (n % i == 0L || n % (i + 2) == 0L) return false
            i += 6
        }
        return true
    }
}
''', "assertEquals(listOf(2, 3, 5, 7), Primes.sieve(10))\n        assertTrue(Primes.isPrime(97))")

algo("fast_power", "Potencia rapida modular", MATH, "Exponenciacao em O(log n), com modulo opcional.", "FastPower", r'''
/** Exponenciacao binaria. */
object FastPower {
    fun pow(base: Long, exponent: Long, modulus: Long = Long.MAX_VALUE): Long {
        var result = 1L
        var b = base % modulus
        var e = exponent
        while (e > 0) {
            if (e and 1L == 1L) result = (result * b) % modulus
            b = (b * b) % modulus
            e = e shr 1
        }
        return result
    }
}
''', "assertEquals(1024L, FastPower.pow(2, 10))\n        assertEquals(43L, FastPower.pow(3, 5, 50))")

algo("statistics", "Estatistica descritiva", MATH, "Media, mediana, moda, desvio padrao, percentis e normalizacao.", "Statistics", r'''
import kotlin.math.sqrt

/** Estatisticas basicas para listas de numeros. */
object Statistics {
    fun mean(values: List<Double>): Double = if (values.isEmpty()) 0.0 else values.sum() / values.size

    fun median(values: List<Double>): Double {
        if (values.isEmpty()) return 0.0
        val sorted = values.sorted()
        val middle = sorted.size / 2
        return if (sorted.size % 2 == 0) (sorted[middle - 1] + sorted[middle]) / 2 else sorted[middle]
    }

    fun mode(values: List<Double>): Double? = values.groupingBy { it }.eachCount().maxByOrNull { it.value }?.key

    fun variance(values: List<Double>): Double {
        if (values.size < 2) return 0.0
        val m = mean(values)
        return values.sumOf { (it - m) * (it - m) } / (values.size - 1)
    }

    fun standardDeviation(values: List<Double>): Double = sqrt(variance(values))

    fun percentile(values: List<Double>, p: Double): Double {
        if (values.isEmpty()) return 0.0
        val sorted = values.sorted()
        val rank = (p / 100.0) * (sorted.size - 1)
        val low = rank.toInt()
        val high = minOf(low + 1, sorted.size - 1)
        return sorted[low] + (sorted[high] - sorted[low]) * (rank - low)
    }

    fun normalize(values: List<Double>): List<Double> {
        val min = values.minOrNull() ?: return values
        val max = values.maxOrNull() ?: return values
        val range = max - min
        return values.map { if (range == 0.0) 0.0 else (it - min) / range }
    }
}
''', "assertEquals(2.5, Statistics.median(listOf(1.0, 2.0, 3.0, 4.0)), 0.001)\n        assertEquals(2.5, Statistics.mean(listOf(1.0, 2.0, 3.0, 4.0)), 0.001)")

algo("moving_average", "Media movel", MATH, "Suaviza series temporais (sensores, precos).", "MovingAverage", r'''
/** Media movel simples e exponencial. */
object MovingAverage {
    fun simple(values: List<Double>, window: Int): List<Double> {
        require(window > 0)
        if (values.size < window) return emptyList()
        var sum = values.take(window).sum()
        val result = mutableListOf(sum / window)
        for (i in window until values.size) {
            sum += values[i] - values[i - window]
            result.add(sum / window)
        }
        return result
    }

    fun exponential(values: List<Double>, alpha: Double = 0.3): List<Double> {
        if (values.isEmpty()) return emptyList()
        val result = mutableListOf(values.first())
        for (i in 1 until values.size) result.add(alpha * values[i] + (1 - alpha) * result.last())
        return result
    }
}
''', "assertEquals(listOf(2.0, 3.0), MovingAverage.simple(listOf(1.0, 2.0, 3.0, 4.0), 3))")

algo("linear_regression", "Regressao linear", MATH, "Tendencia e previsao por minimos quadrados.", "LinearRegression", r'''
/** Regressao linear simples y = a + b * x. */
class LinearRegression(x: List<Double>, y: List<Double>) {
    val slope: Double
    val intercept: Double

    init {
        require(x.size == y.size && x.size >= 2)
        val meanX = x.average()
        val meanY = y.average()
        var numerator = 0.0
        var denominator = 0.0
        for (i in x.indices) {
            numerator += (x[i] - meanX) * (y[i] - meanY)
            denominator += (x[i] - meanX) * (x[i] - meanX)
        }
        slope = if (denominator == 0.0) 0.0 else numerator / denominator
        intercept = meanY - slope * meanX
    }

    fun predict(x: Double) = intercept + slope * x
}
''', "assertEquals(10.0, LinearRegression(listOf(1.0, 2.0, 3.0), listOf(2.0, 4.0, 6.0)).predict(5.0), 0.001)")

algo("haversine", "Distancia geografica (Haversine)", MATH, "Distancia em km entre duas coordenadas GPS.", "Haversine", r'''
import kotlin.math.asin
import kotlin.math.cos
import kotlin.math.pow
import kotlin.math.sin
import kotlin.math.sqrt

/** Distancia entre dois pontos na superficie da Terra. */
object Haversine {
    private const val EARTH_RADIUS_KM = 6371.0

    fun distanceKm(lat1: Double, lon1: Double, lat2: Double, lon2: Double): Double {
        val dLat = Math.toRadians(lat2 - lat1)
        val dLon = Math.toRadians(lon2 - lon1)
        val a = sin(dLat / 2).pow(2) + cos(Math.toRadians(lat1)) * cos(Math.toRadians(lat2)) * sin(dLon / 2).pow(2)
        return 2 * EARTH_RADIUS_KM * asin(sqrt(a))
    }

    /** Estimativa de tempo em minutos para uma velocidade media. */
    fun etaMinutes(distanceKm: Double, speedKmh: Double = 30.0): Int = (distanceKm / speedKmh * 60).toInt()
}
''', "assertEquals(357.0, Haversine.distanceKm(-23.5505, -46.6333, -22.9068, -43.1729), 5.0)")

algo("unit_converter", "Conversor de unidades", MATH, "Temperatura, distancia, peso, volume e velocidade.", "UnitConverter", r'''
/** Conversoes de unidades comuns. */
object UnitConverter {
    fun celsiusToFahrenheit(c: Double) = c * 9 / 5 + 32
    fun fahrenheitToCelsius(f: Double) = (f - 32) * 5 / 9
    fun kmToMiles(km: Double) = km * 0.621371
    fun milesToKm(miles: Double) = miles / 0.621371
    fun kgToPounds(kg: Double) = kg * 2.20462
    fun poundsToKg(lb: Double) = lb / 2.20462
    fun litersToGallons(l: Double) = l * 0.264172
    fun kmhToMs(kmh: Double) = kmh / 3.6
    fun bytesToReadable(bytes: Long): String {
        val units = listOf("B", "KB", "MB", "GB", "TB")
        var value = bytes.toDouble()
        var index = 0
        while (value >= 1024 && index < units.lastIndex) {
            value /= 1024
            index++
        }
        return "%.1f %s".format(value, units[index])
    }
}
''', "assertEquals(212.0, UnitConverter.celsiusToFahrenheit(100.0), 0.001)")

algo("health_calc", "Calculos de saude", MATH, "IMC, taxa metabolica basal, agua diaria e frequencia cardiaca alvo.", "HealthCalculator", r'''
/** Formulas de saude e fitness. Nao substituem avaliacao profissional. */
object HealthCalculator {
    fun bmi(weightKg: Double, heightM: Double): Double = weightKg / (heightM * heightM)

    fun bmiCategory(bmi: Double): String = when {
        bmi < 18.5 -> "Abaixo do peso"
        bmi < 25 -> "Peso normal"
        bmi < 30 -> "Sobrepeso"
        else -> "Obesidade"
    }

    /** Taxa metabolica basal (Mifflin-St Jeor), em kcal/dia. */
    fun bmr(weightKg: Double, heightCm: Double, age: Int, male: Boolean): Double =
        10 * weightKg + 6.25 * heightCm - 5 * age + if (male) 5 else -161

    /** Agua recomendada em litros (35 ml por kg). */
    fun dailyWaterLiters(weightKg: Double) = weightKg * 0.035

    /** Faixa de frequencia cardiaca alvo (50% a 85% da maxima). */
    fun targetHeartRate(age: Int): IntRange {
        val max = 220 - age
        return (max * 0.5).toInt()..(max * 0.85).toInt()
    }
}
''', "assertEquals(\"Peso normal\", HealthCalculator.bmiCategory(HealthCalculator.bmi(70.0, 1.75)))")

# ------------------------------------------------------------------ financeiro
algo("loan_price", "Financiamento (Tabela Price e SAC)", FIN, "Parcelas, juros e amortizacao de emprestimos.", "LoanCalculator", r'''
import kotlin.math.pow

/** Calculo de financiamentos. Taxas em decimal ao mes (1% = 0.01). */
object LoanCalculator {
    data class Installment(val number: Int, val payment: Double, val interest: Double, val amortization: Double, val balance: Double)

    /** Parcela fixa da Tabela Price. */
    fun pricePayment(principal: Double, monthlyRate: Double, months: Int): Double =
        if (monthlyRate == 0.0) principal / months
        else principal * monthlyRate / (1 - (1 + monthlyRate).pow(-months))

    fun priceSchedule(principal: Double, monthlyRate: Double, months: Int): List<Installment> {
        val payment = pricePayment(principal, monthlyRate, months)
        var balance = principal
        return (1..months).map { n ->
            val interest = balance * monthlyRate
            val amortization = payment - interest
            balance -= amortization
            Installment(n, payment, interest, amortization, balance.coerceAtLeast(0.0))
        }
    }

    /** Sistema de Amortizacao Constante. */
    fun sacSchedule(principal: Double, monthlyRate: Double, months: Int): List<Installment> {
        val amortization = principal / months
        var balance = principal
        return (1..months).map { n ->
            val interest = balance * monthlyRate
            balance -= amortization
            Installment(n, amortization + interest, interest, amortization, balance.coerceAtLeast(0.0))
        }
    }
}
''', "assertEquals(1000.0, LoanCalculator.pricePayment(12000.0, 0.0, 12), 0.001)")

algo("compound_interest", "Juros compostos e investimentos", FIN, "Montante, aportes mensais e taxa equivalente.", "CompoundInterest", r'''
import kotlin.math.pow

/** Calculos de juros compostos. Taxas em decimal. */
object CompoundInterest {
    fun futureValue(principal: Double, rate: Double, periods: Int): Double = principal * (1 + rate).pow(periods)

    /** Montante com aporte mensal fixo ao final de cada periodo. */
    fun withContributions(principal: Double, monthly: Double, rate: Double, months: Int): Double {
        if (rate == 0.0) return principal + monthly * months
        return principal * (1 + rate).pow(months) + monthly * (((1 + rate).pow(months) - 1) / rate)
    }

    /** Converte taxa anual em mensal equivalente. */
    fun annualToMonthly(annualRate: Double): Double = (1 + annualRate).pow(1.0 / 12) - 1
}
''', "assertEquals(1210.0, CompoundInterest.futureValue(1000.0, 0.1, 2), 0.001)")

algo("bill_split", "Divisao de contas", FIN, "Divide valores com gorjeta e distribui centavos sem perdas.", "BillSplitter", r'''
import kotlin.math.roundToLong

/** Divide uma conta entre pessoas, ajustando os centavos restantes. */
object BillSplitter {
    fun split(total: Double, people: Int, tipPercent: Double = 0.0): List<Double> {
        require(people > 0)
        val cents = (total * (1 + tipPercent / 100) * 100).roundToLong()
        val base = cents / people
        val remainder = (cents % people).toInt()
        return (0 until people).map { (base + if (it < remainder) 1 else 0) / 100.0 }
    }
}
''', "assertEquals(10.0, BillSplitter.split(30.0, 3).sum() / 3, 0.001)")

algo("expense_summary", "Resumo de gastos por categoria", FIN, "Agrupa valores, calcula percentuais e maiores gastos.", "ExpenseSummary", r'''
/** Agregacao de despesas por categoria. */
object ExpenseSummary {
    data class Expense(val category: String, val amount: Double)

    fun totals(expenses: List<Expense>): Map<String, Double> =
        expenses.groupBy { it.category }.mapValues { (_, list) -> list.sumOf { it.amount } }
            .toList().sortedByDescending { it.second }.toMap()

    fun percentages(expenses: List<Expense>): Map<String, Double> {
        val total = expenses.sumOf { it.amount }
        if (total == 0.0) return emptyMap()
        return totals(expenses).mapValues { it.value / total * 100 }
    }
}
''', "assertEquals(30.0, ExpenseSummary.totals(listOf(ExpenseSummary.Expense(\"a\", 10.0), ExpenseSummary.Expense(\"a\", 20.0)))[\"a\"]!!, 0.001)")

# ------------------------------------------------------------------ estruturas
algo("lru_cache", "Cache LRU", DS, "Mantem os itens usados mais recentemente com limite de tamanho.", "LruCacheMap", r'''
/** Cache com politica LRU baseado em LinkedHashMap. */
class LruCacheMap<K, V>(private val capacity: Int) : LinkedHashMap<K, V>(capacity, 0.75f, true) {
    override fun removeEldestEntry(eldest: MutableMap.MutableEntry<K, V>?): Boolean = size > capacity
}
''', "val cache = LruCacheMap<String, Int>(2)\n        cache[\"a\"] = 1\n        cache[\"b\"] = 2\n        cache[\"a\"]\n        cache[\"c\"] = 3\n        assertFalse(cache.containsKey(\"b\"))")

algo("circular_buffer", "Buffer circular", DS, "Fila de tamanho fixo para ultimas N leituras.", "CircularBuffer", r'''
/** Buffer circular de capacidade fixa. */
class CircularBuffer<T>(private val capacity: Int) {
    private val data = ArrayList<T>(capacity)
    private var start = 0

    fun add(value: T) {
        if (data.size < capacity) {
            data.add(value)
        } else {
            data[start] = value
            start = (start + 1) % capacity
        }
    }

    fun toList(): List<T> = List(data.size) { data[(start + it) % data.size] }

    val size: Int get() = data.size
}
''', "val b = CircularBuffer<Int>(2)\n        b.add(1)\n        b.add(2)\n        b.add(3)\n        assertEquals(listOf(2, 3), b.toList())")

algo("priority_queue", "Fila de prioridade de tarefas", DS, "Ordena tarefas por prioridade e prazo.", "TaskQueue", r'''
import java.util.PriorityQueue

/** Fila de tarefas por prioridade (maior primeiro) e prazo (mais cedo primeiro). */
class TaskQueue {
    data class Task(val title: String, val priority: Int, val dueAt: Long)

    private val queue = PriorityQueue(compareByDescending<Task> { it.priority }.thenBy { it.dueAt })

    fun add(task: Task) = queue.add(task)
    fun next(): Task? = queue.poll()
    fun peek(): Task? = queue.peek()
    val size: Int get() = queue.size
}
''', "val q = TaskQueue()\n        q.add(TaskQueue.Task(\"b\", 1, 0))\n        q.add(TaskQueue.Task(\"a\", 5, 0))\n        assertEquals(\"a\", q.next()!!.title)")

algo("undo_redo", "Desfazer e refazer", DS, "Pilhas de historico para editores e formularios.", "UndoRedoStack", r'''
/** Historico com desfazer/refazer. */
class UndoRedoStack<T>(initial: T, private val limit: Int = 100) {
    private val undo = ArrayDeque<T>()
    private val redo = ArrayDeque<T>()
    var current: T = initial
        private set

    fun push(state: T) {
        undo.addLast(current)
        if (undo.size > limit) undo.removeFirst()
        current = state
        redo.clear()
    }

    fun undo(): T {
        if (undo.isNotEmpty()) {
            redo.addLast(current)
            current = undo.removeLast()
        }
        return current
    }

    fun redo(): T {
        if (redo.isNotEmpty()) {
            undo.addLast(current)
            current = redo.removeLast()
        }
        return current
    }

    val canUndo get() = undo.isNotEmpty()
    val canRedo get() = redo.isNotEmpty()
}
''', "val h = UndoRedoStack(\"a\")\n        h.push(\"b\")\n        assertEquals(\"a\", h.undo())\n        assertEquals(\"b\", h.redo())")

algo("bloom_filter", "Bloom Filter", DS, "Teste rapido de pertinencia com pouca memoria.", "BloomFilter", r'''
import java.util.BitSet

/** Filtro de Bloom: pode ter falso positivo, nunca falso negativo. */
class BloomFilter(private val size: Int = 10_000, private val hashes: Int = 3) {
    private val bits = BitSet(size)

    private fun positions(value: String): List<Int> {
        val h1 = value.hashCode()
        val h2 = value.reversed().hashCode() or 1
        return (0 until hashes).map { Math.floorMod(h1 + it * h2, size) }
    }

    fun add(value: String) = positions(value).forEach { bits.set(it) }

    fun mightContain(value: String) = positions(value).all { bits.get(it) }
}
''', "val f = BloomFilter()\n        f.add(\"kotlin\")\n        assertTrue(f.mightContain(\"kotlin\"))")

# ------------------------------------------------------------------ utilitarios
algo("debounce", "Debounce e throttle", UTIL, "Evita chamadas repetidas (busca enquanto digita, cliques duplos).", "Debouncer", r'''
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/** Executa a acao somente apos [waitMs] sem novas chamadas. */
class Debouncer(private val scope: CoroutineScope, private val waitMs: Long = 400L) {
    private var job: Job? = null

    fun submit(action: suspend () -> Unit) {
        job?.cancel()
        job = scope.launch {
            delay(waitMs)
            action()
        }
    }
}

/** Permite no maximo uma execucao a cada [intervalMs]. */
class Throttler(private val intervalMs: Long = 600L) {
    private var last = 0L

    fun tryRun(action: () -> Unit): Boolean {
        val now = System.currentTimeMillis()
        if (now - last < intervalMs) return false
        last = now
        action()
        return true
    }
}
''', "val t = Throttler(10_000)\n        assertTrue(t.tryRun { })\n        assertFalse(t.tryRun { })")

algo("retry_backoff", "Repetir com backoff exponencial", UTIL, "Tenta novamente operacoes de rede com espera crescente.", "RetryPolicy", r'''
import kotlinx.coroutines.delay

/** Repete uma operacao suspensa com espera exponencial entre tentativas. */
object RetryPolicy {
    suspend fun <T> retry(
        times: Int = 3,
        initialDelayMs: Long = 500L,
        factor: Double = 2.0,
        maxDelayMs: Long = 8_000L,
        block: suspend () -> T
    ): T {
        var currentDelay = initialDelayMs
        repeat(times - 1) {
            try {
                return block()
            } catch (e: Exception) {
                delay(currentDelay)
                currentDelay = (currentDelay * factor).toLong().coerceAtMost(maxDelayMs)
            }
        }
        return block()
    }
}
''', "assertEquals(1, kotlinx.coroutines.runBlocking { RetryPolicy.retry(times = 2, initialDelayMs = 1) { 1 } })")

algo("rate_limiter", "Limitador de taxa (Token Bucket)", UTIL, "Controla quantas requisicoes podem ser feitas por segundo.", "TokenBucket", r'''
/** Token bucket: capacidade maxima e reposicao por segundo. */
class TokenBucket(private val capacity: Int, private val refillPerSecond: Double) {
    private var tokens = capacity.toDouble()
    private var lastRefill = System.nanoTime()

    @Synchronized
    fun tryAcquire(): Boolean {
        val now = System.nanoTime()
        tokens = minOf(capacity.toDouble(), tokens + (now - lastRefill) / 1e9 * refillPerSecond)
        lastRefill = now
        if (tokens < 1) return false
        tokens -= 1
        return true
    }
}
''', "val b = TokenBucket(1, 0.0)\n        assertTrue(b.tryAcquire())\n        assertFalse(b.tryAcquire())")

algo("id_generator", "Geracao de IDs", UTIL, "UUID, IDs curtos legiveis e codigos de pedido.", "IdGenerator", r'''
import java.security.SecureRandom
import java.util.UUID

/** Geradores de identificadores. */
object IdGenerator {
    private const val ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    private val random = SecureRandom()

    fun uuid(): String = UUID.randomUUID().toString()

    /** Codigo curto sem caracteres ambiguos (ex.: pedidos, cupons). */
    fun shortCode(length: Int = 8): String = (1..length).map { ALPHABET[random.nextInt(ALPHABET.length)] }.joinToString("")

    /** Codigo numerico (ex.: verificacao por SMS). */
    fun numericCode(length: Int = 6): String = (1..length).map { random.nextInt(10) }.joinToString("")
}
''', "assertEquals(8, IdGenerator.shortCode().length)")

algo("date_utils", "Utilitarios de data", UTIL, "Idade, dias entre datas, dias uteis e inicio da semana.", "DateUtils", r'''
import java.util.Calendar
import java.util.concurrent.TimeUnit

/** Calculos com datas usando java.util.Calendar (compativel com todas as APIs). */
object DateUtils {
    fun ageFrom(birthMillis: Long, now: Long = System.currentTimeMillis()): Int {
        val birth = Calendar.getInstance().apply { timeInMillis = birthMillis }
        val today = Calendar.getInstance().apply { timeInMillis = now }
        var age = today.get(Calendar.YEAR) - birth.get(Calendar.YEAR)
        if (today.get(Calendar.DAY_OF_YEAR) < birth.get(Calendar.DAY_OF_YEAR)) age--
        return age
    }

    fun daysBetween(startMillis: Long, endMillis: Long): Long = TimeUnit.MILLISECONDS.toDays(endMillis - startMillis)

    fun businessDaysBetween(startMillis: Long, endMillis: Long): Int {
        val calendar = Calendar.getInstance().apply { timeInMillis = startMillis }
        var count = 0
        while (calendar.timeInMillis < endMillis) {
            val day = calendar.get(Calendar.DAY_OF_WEEK)
            if (day != Calendar.SATURDAY && day != Calendar.SUNDAY) count++
            calendar.add(Calendar.DAY_OF_MONTH, 1)
        }
        return count
    }

    fun startOfDay(millis: Long): Long = Calendar.getInstance().apply {
        timeInMillis = millis
        set(Calendar.HOUR_OF_DAY, 0)
        set(Calendar.MINUTE, 0)
        set(Calendar.SECOND, 0)
        set(Calendar.MILLISECOND, 0)
    }.timeInMillis
}
''', "assertEquals(1L, DateUtils.daysBetween(0, 86_400_000))")

algo("pagination", "Paginacao", UTIL, "Divide listas em paginas e calcula total de paginas.", "Paginator", r'''
/** Paginacao em memoria. Paginas comecam em 1. */
class Paginator<T>(private val items: List<T>, private val pageSize: Int = 20) {
    val totalPages: Int get() = if (items.isEmpty()) 1 else (items.size + pageSize - 1) / pageSize

    fun page(number: Int): List<T> {
        val from = ((number - 1) * pageSize).coerceIn(0, items.size)
        val to = (from + pageSize).coerceAtMost(items.size)
        return items.subList(from, to)
    }

    fun hasNext(number: Int) = number < totalPages
}
''', "val p = Paginator((1..45).toList(), 20)\n        assertEquals(3, p.totalPages)\n        assertEquals(5, p.page(3).size)")

algo("shuffle_random", "Embaralhar e sortear", UTIL, "Fisher-Yates, sorteio ponderado e amostragem por reservatorio.", "RandomUtils", r'''
import kotlin.random.Random

/** Embaralhamento e sorteios. */
object RandomUtils {
    fun <T> shuffle(items: List<T>, random: Random = Random.Default): List<T> {
        val result = items.toMutableList()
        for (i in result.lastIndex downTo 1) {
            val j = random.nextInt(i + 1)
            val temp = result[i]
            result[i] = result[j]
            result[j] = temp
        }
        return result
    }

    /** Sorteia um item considerando pesos (ex.: roleta de premios). */
    fun <T> weightedPick(items: List<Pair<T, Double>>, random: Random = Random.Default): T {
        val total = items.sumOf { it.second }
        var roll = random.nextDouble() * total
        for ((item, weight) in items) {
            roll -= weight
            if (roll <= 0) return item
        }
        return items.last().first
    }

    /** Amostra k itens de uma sequencia de tamanho desconhecido. */
    fun <T> reservoirSample(items: Sequence<T>, k: Int, random: Random = Random.Default): List<T> {
        val reservoir = ArrayList<T>(k)
        items.forEachIndexed { index, item ->
            if (index < k) reservoir.add(item) else {
                val j = random.nextInt(index + 1)
                if (j < k) reservoir[j] = item
            }
        }
        return reservoir
    }
}
''', "assertEquals(setOf(1, 2, 3), RandomUtils.shuffle(listOf(1, 2, 3)).toSet())")

# ------------------------------------------------------------------ validacao e seguranca
algo("luhn", "Validacao de cartao (Luhn)", VAL, "Valida numeros de cartao e identifica a bandeira.", "CardValidator", r'''
/** Validacao de cartoes pelo algoritmo de Luhn. */
object CardValidator {
    fun isValid(number: String): Boolean {
        val digits = number.filter { it.isDigit() }
        if (digits.length !in 12..19) return false
        var sum = 0
        digits.reversed().forEachIndexed { index, char ->
            var value = char - '0'
            if (index % 2 == 1) {
                value *= 2
                if (value > 9) value -= 9
            }
            sum += value
        }
        return sum % 10 == 0
    }

    fun brand(number: String): String {
        val digits = number.filter { it.isDigit() }
        return when {
            digits.startsWith("4") -> "Visa"
            digits.take(2).toIntOrNull() in 51..55 || digits.take(4).toIntOrNull() in 2221..2720 -> "Mastercard"
            digits.startsWith("34") || digits.startsWith("37") -> "American Express"
            digits.startsWith("636368") || digits.startsWith("438935") || digits.startsWith("504175") -> "Elo"
            digits.startsWith("606282") -> "Hipercard"
            else -> "Desconhecida"
        }
    }

    fun mask(number: String): String {
        val digits = number.filter { it.isDigit() }
        return if (digits.length < 4) digits else "**** **** **** " + digits.takeLast(4)
    }
}
''', "assertTrue(CardValidator.isValid(\"4539 1488 0343 6467\"))\n        assertEquals(\"Visa\", CardValidator.brand(\"4539148803436467\"))")

algo("iban", "Validacao de IBAN", VAL, "Valida IBAN europeu (inclui Portugal) pelo modulo 97.", "IbanValidator", r'''
import java.math.BigInteger

/** Validacao de IBAN conforme ISO 13616. */
object IbanValidator {
    fun isValid(iban: String): Boolean {
        val clean = iban.replace(" ", "").uppercase()
        if (clean.length < 15 || clean.length > 34 || !clean.all { it.isLetterOrDigit() }) return false
        val rearranged = clean.drop(4) + clean.take(4)
        val numeric = rearranged.map { if (it.isDigit()) it.toString() else (it - 'A' + 10).toString() }.joinToString("")
        return BigInteger(numeric).mod(BigInteger.valueOf(97)) == BigInteger.ONE
    }
}
''', "assertTrue(IbanValidator.isValid(\"GB82 WEST 1234 5698 7654 32\"))")

algo("password_strength", "Forca de senha", VAL, "Pontuacao de 0 a 4 com dicas de melhoria.", "PasswordStrength", r'''
/** Avalia a forca de uma senha. */
object PasswordStrength {
    data class Result(val score: Int, val label: String, val tips: List<String>)

    fun evaluate(password: String): Result {
        val tips = mutableListOf<String>()
        var score = 0
        if (password.length >= 8) score++ else tips.add("Use pelo menos 8 caracteres")
        if (password.length >= 12) score++
        if (password.any { it.isUpperCase() } && password.any { it.isLowerCase() }) score++ else tips.add("Misture letras maiusculas e minusculas")
        if (password.any { it.isDigit() }) score++ else tips.add("Inclua numeros")
        if (password.any { !it.isLetterOrDigit() }) score++ else tips.add("Inclua simbolos")
        val final = score.coerceAtMost(4)
        val label = listOf("Muito fraca", "Fraca", "Razoavel", "Forte", "Muito forte")[final]
        return Result(final, label, tips)
    }
}
''', "assertEquals(4, PasswordStrength.evaluate(\"Abcdef123456!\").score)")

algo("hashing", "Hash e codificacao", VAL, "SHA-256, MD5, HMAC e Base64.", "HashUtils", r'''
import java.security.MessageDigest
import java.util.Base64
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

/** Funcoes de hash e codificacao. MD5 apenas para checksums, nunca para senhas. */
object HashUtils {
    private fun hex(bytes: ByteArray) = bytes.joinToString("") { "%02x".format(it) }

    fun sha256(text: String): String = hex(MessageDigest.getInstance("SHA-256").digest(text.toByteArray()))

    fun md5(text: String): String = hex(MessageDigest.getInstance("MD5").digest(text.toByteArray()))

    fun hmacSha256(key: String, message: String): String {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(key.toByteArray(), "HmacSHA256"))
        return hex(mac.doFinal(message.toByteArray()))
    }

    fun base64Encode(text: String): String = Base64.getEncoder().encodeToString(text.toByteArray())

    fun base64Decode(text: String): String = String(Base64.getDecoder().decode(text))
}
''', "assertEquals(\"900150983cd24fb0d6963f7d28e17f72\", HashUtils.md5(\"abc\"))")

algo("masks", "Mascaras de entrada", VAL, "Aplica mascaras como telefone, CPF, CEP e cartao.", "InputMask", r'''
/** Aplica mascaras usando '#' como digito. Ex.: "(##) #####-####". */
object InputMask {
    const val PHONE_BR = "(##) #####-####"
    const val CPF = "###.###.###-##"
    const val CNPJ = "##.###.###/####-##"
    const val CEP = "#####-###"
    const val POSTAL_PT = "####-###"
    const val CARD = "#### #### #### ####"

    fun apply(value: String, mask: String): String {
        val digits = value.filter { it.isDigit() }
        val result = StringBuilder()
        var index = 0
        for (char in mask) {
            if (index >= digits.length) break
            if (char == '#') result.append(digits[index++]) else result.append(char)
        }
        return result.toString()
    }
}
''', "assertEquals(\"123.456.789-09\", InputMask.apply(\"12345678909\", InputMask.CPF))")

# ------------------------------------------------------------------ recomendacao e dados
algo("cosine_recommender", "Recomendacao por similaridade", ML, "Sugere itens parecidos usando similaridade do cosseno.", "Recommender", r'''
import kotlin.math.sqrt

/** Recomendacao baseada em vetores de caracteristicas. */
object Recommender {
    fun cosine(a: DoubleArray, b: DoubleArray): Double {
        var dot = 0.0
        var normA = 0.0
        var normB = 0.0
        for (i in a.indices) {
            dot += a[i] * b[i]
            normA += a[i] * a[i]
            normB += b[i] * b[i]
        }
        return if (normA == 0.0 || normB == 0.0) 0.0 else dot / (sqrt(normA) * sqrt(normB))
    }

    /** Retorna as chaves dos [k] itens mais parecidos com [target]. */
    fun <K> similar(target: DoubleArray, catalog: Map<K, DoubleArray>, k: Int = 5): List<K> =
        catalog.entries.sortedByDescending { cosine(target, it.value) }.take(k).map { it.key }
}
''', "assertEquals(1.0, Recommender.cosine(doubleArrayOf(1.0, 2.0), doubleArrayOf(2.0, 4.0)), 0.0001)")

algo("kmeans", "Agrupamento K-Means", ML, "Agrupa pontos em k grupos (clientes, regioes).", "KMeans", r'''
import kotlin.random.Random

/** K-Means em 2 dimensoes. */
object KMeans {
    data class Point(val x: Double, val y: Double)

    fun cluster(points: List<Point>, k: Int, iterations: Int = 50, seed: Int = 42): List<Int> {
        if (points.isEmpty()) return emptyList()
        val random = Random(seed)
        var centers = points.shuffled(random).take(k)
        var labels = IntArray(points.size)
        repeat(iterations) {
            labels = IntArray(points.size) { i ->
                centers.indices.minByOrNull { c ->
                    val dx = points[i].x - centers[c].x
                    val dy = points[i].y - centers[c].y
                    dx * dx + dy * dy
                }!!
            }
            centers = centers.indices.map { c ->
                val members = points.filterIndexed { i, _ -> labels[i] == c }
                if (members.isEmpty()) centers[c] else Point(members.map { it.x }.average(), members.map { it.y }.average())
            }
        }
        return labels.toList()
    }
}
''', "val l = KMeans.cluster(listOf(KMeans.Point(0.0, 0.0), KMeans.Point(0.1, 0.0), KMeans.Point(10.0, 10.0)), 2)\n        assertEquals(l[0], l[1])\n        assertNotEquals(l[0], l[2])")

algo("kalman", "Filtro de Kalman 1D", ML, "Suaviza leituras ruidosas de GPS e sensores.", "KalmanFilter", r'''
/** Filtro de Kalman unidimensional. */
class KalmanFilter(
    private val processNoise: Double = 1e-3,
    private val measurementNoise: Double = 1e-1,
    private var estimate: Double = 0.0,
    private var errorCovariance: Double = 1.0
) {
    fun update(measurement: Double): Double {
        errorCovariance += processNoise
        val gain = errorCovariance / (errorCovariance + measurementNoise)
        estimate += gain * (measurement - estimate)
        errorCovariance *= (1 - gain)
        return estimate
    }
}
''', "val k = KalmanFilter(estimate = 10.0)\n        val v = (1..20).map { k.update(10.0) }.last()\n        assertEquals(10.0, v, 0.001)")

algo("json_flatten", "Achatar mapas aninhados", ML, "Transforma estruturas aninhadas em chaves com ponto (a.b.c).", "MapFlattener", r'''
/** Converte mapas e listas aninhados em um mapa plano. */
object MapFlattener {
    fun flatten(value: Any?, prefix: String = "", out: MutableMap<String, Any?> = linkedMapOf()): Map<String, Any?> {
        when (value) {
            is Map<*, *> -> value.forEach { (k, v) -> flatten(v, if (prefix.isEmpty()) "$k" else "$prefix.$k", out) }
            is List<*> -> value.forEachIndexed { i, v -> flatten(v, "$prefix[$i]", out) }
            else -> out[prefix] = value
        }
        return out
    }
}
''', "assertEquals(1, MapFlattener.flatten(mapOf(\"a\" to mapOf(\"b\" to 1)))[\"a.b\"])")

# ------------------------------------------------------------------ v1.1: novos algoritmos
HEALTH = "Saude e esportes"

algo("spaced_repetition", "Repeticao espacada (SM-2)", UTIL,
     "Calcula a proxima revisao de um cartao de estudo (algoritmo SuperMemo 2).", "SpacedRepetition", r'''
/** Estado de um cartao de estudo. [interval] em dias. */
data class CardState(val repetitions: Int = 0, val interval: Int = 0, val easiness: Double = 2.5)

/** Algoritmo SM-2: [quality] vai de 0 (esqueceu) a 5 (resposta perfeita). */
object SpacedRepetition {
    fun review(card: CardState, quality: Int): CardState {
        val q = quality.coerceIn(0, 5)
        val easiness = (card.easiness + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))).coerceAtLeast(1.3)
        if (q < 3) return CardState(repetitions = 0, interval = 1, easiness = easiness)
        val repetitions = card.repetitions + 1
        val interval = when (repetitions) {
            1 -> 1
            2 -> 6
            else -> Math.round(card.interval * card.easiness).toInt()
        }
        return CardState(repetitions, interval, easiness)
    }
}
''', '''var card = CardState()
        card = SpacedRepetition.review(card, 5)
        assertEquals(1, card.interval)
        card = SpacedRepetition.review(card, 5)
        assertEquals(6, card.interval)
        card = SpacedRepetition.review(card, 4)
        assertTrue(card.interval > 6)
        assertEquals(1, SpacedRepetition.review(card, 1).interval)''')

algo("elo_rating", "Ranking Elo", MATH, "Pontuacao de jogadores ou times apos cada partida (xadrez, games, torneios).",
     "EloRating", r'''
import kotlin.math.pow

/** Sistema Elo: [k] controla o quanto cada partida altera a pontuacao. */
object EloRating {
    /** Probabilidade de A vencer B. */
    fun expected(ratingA: Double, ratingB: Double): Double = 1.0 / (1.0 + 10.0.pow((ratingB - ratingA) / 400.0))

    /** Novas pontuacoes (A, B). [scoreA]: 1 vitoria, 0.5 empate, 0 derrota. */
    fun update(ratingA: Double, ratingB: Double, scoreA: Double, k: Double = 32.0): Pair<Double, Double> {
        val expectedA = expected(ratingA, ratingB)
        val newA = ratingA + k * (scoreA - expectedA)
        val newB = ratingB + k * ((1 - scoreA) - (1 - expectedA))
        return newA to newB
    }
}
''', '''assertEquals(0.5, EloRating.expected(1500.0, 1500.0), 1e-9)
        val (a, b) = EloRating.update(1500.0, 1500.0, 1.0)
        assertEquals(1516.0, a, 1e-9)
        assertEquals(1484.0, b, 1e-9)''')

algo("password_generator", "Gerador de senhas", VAL,
     "Gera senhas aleatorias seguras (SecureRandom) com letras, numeros e simbolos.", "PasswordGenerator", r'''
import java.security.SecureRandom

/** Gera senhas garantindo ao menos um caractere de cada grupo escolhido. */
object PasswordGenerator {
    private const val LOWER = "abcdefghijkmnopqrstuvwxyz"
    private const val UPPER = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    private const val DIGITS = "23456789"
    private const val SYMBOLS = "!@#$%&*?-_+="
    private val random = SecureRandom()

    fun generate(length: Int = 16, upper: Boolean = true, digits: Boolean = true, symbols: Boolean = true): String {
        val groups = listOfNotNull(LOWER, UPPER.takeIf { upper }, DIGITS.takeIf { digits }, SYMBOLS.takeIf { symbols })
        val size = length.coerceAtLeast(groups.size)
        val chars = groups.map { it[random.nextInt(it.length)] }.toMutableList()
        val all = groups.joinToString("")
        while (chars.size < size) chars.add(all[random.nextInt(all.length)])
        // Embaralha para que os caracteres obrigatorios nao fiquem sempre no inicio.
        for (i in chars.size - 1 downTo 1) {
            val j = random.nextInt(i + 1)
            val temp = chars[i]
            chars[i] = chars[j]
            chars[j] = temp
        }
        return chars.joinToString("")
    }
}
''', '''val password = PasswordGenerator.generate(20)
        assertEquals(20, password.length)
        assertTrue(password.any { it.isDigit() })
        assertTrue(password.any { it.isUpperCase() })
        assertTrue(password.any { !it.isLetterOrDigit() })
        assertTrue(PasswordGenerator.generate(8, upper = false, digits = false, symbols = false).all { it.isLowerCase() })''')

algo("color_tools", "Cores e contraste (WCAG)", UTIL,
     "Converte HEX/RGB, clareia, escurece e mede o contraste entre cores para acessibilidade.", "ColorTools", r'''
import kotlin.math.pow

/** Utilitarios de cor sem depender do Android (cores como 0xRRGGBB). */
object ColorTools {
    fun parseHex(hex: String): Int = hex.removePrefix("#").takeLast(6).toInt(16)

    fun toHex(rgb: Int): String = "#%06X".format(rgb and 0xFFFFFF)

    private fun channel(value: Int): Double {
        val c = value / 255.0
        return if (c <= 0.03928) c / 12.92 else ((c + 0.055) / 1.055).pow(2.4)
    }

    /** Luminancia relativa (0 = preto, 1 = branco). */
    fun luminance(rgb: Int): Double =
        0.2126 * channel(rgb shr 16 and 0xFF) + 0.7152 * channel(rgb shr 8 and 0xFF) + 0.0722 * channel(rgb and 0xFF)

    /** Razao de contraste entre 1 e 21. O WCAG pede 4.5 para texto normal. */
    fun contrast(a: Int, b: Int): Double {
        val la = luminance(a)
        val lb = luminance(b)
        return (maxOf(la, lb) + 0.05) / (minOf(la, lb) + 0.05)
    }

    /** Mistura a cor com branco (amount > 0) ou preto (amount < 0). */
    fun shade(rgb: Int, amount: Double): Int {
        val target = if (amount >= 0) 255 else 0
        val t = kotlin.math.abs(amount).coerceIn(0.0, 1.0)
        fun mix(c: Int) = (c + (target - c) * t).toInt().coerceIn(0, 255)
        return (mix(rgb shr 16 and 0xFF) shl 16) or (mix(rgb shr 8 and 0xFF) shl 8) or mix(rgb and 0xFF)
    }

    /** Preto ou branco, o que tiver mais contraste com o fundo. */
    fun bestTextColor(background: Int): Int =
        if (contrast(background, 0x000000) >= contrast(background, 0xFFFFFF)) 0x000000 else 0xFFFFFF
}
''', '''assertEquals(21.0, ColorTools.contrast(0x000000, 0xFFFFFF), 0.01)
        assertEquals("#1F6FEB", ColorTools.toHex(ColorTools.parseHex("#1f6feb")))
        assertEquals(0xFFFFFF, ColorTools.bestTextColor(0x0D1B2A))
        assertEquals(0xFFFFFF, ColorTools.shade(0x123456, 1.0))''')

algo("geohash", "Geohash", GRAPH, "Codifica latitude/longitude em texto curto, util para agrupar locais proximos.",
     "Geohash", r'''
/** Codificacao e decodificacao Geohash (base32). */
object Geohash {
    private const val BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

    fun encode(latitude: Double, longitude: Double, precision: Int = 9): String {
        var latRange = doubleArrayOf(-90.0, 90.0)
        var lonRange = doubleArrayOf(-180.0, 180.0)
        val hash = StringBuilder()
        var bit = 0
        var ch = 0
        var even = true
        while (hash.length < precision) {
            val range = if (even) lonRange else latRange
            val value = if (even) longitude else latitude
            val mid = (range[0] + range[1]) / 2
            if (value >= mid) {
                ch = ch or (1 shl (4 - bit))
                range[0] = mid
            } else {
                range[1] = mid
            }
            even = !even
            if (bit < 4) {
                bit++
            } else {
                hash.append(BASE32[ch])
                bit = 0
                ch = 0
            }
        }
        return hash.toString()
    }

    /** Centro aproximado (latitude, longitude) de um geohash. */
    fun decode(hash: String): Pair<Double, Double> {
        val lat = doubleArrayOf(-90.0, 90.0)
        val lon = doubleArrayOf(-180.0, 180.0)
        var even = true
        for (c in hash) {
            val cd = BASE32.indexOf(c)
            for (mask in intArrayOf(16, 8, 4, 2, 1)) {
                val range = if (even) lon else lat
                val mid = (range[0] + range[1]) / 2
                if (cd and mask != 0) range[0] = mid else range[1] = mid
                even = !even
            }
        }
        return (lat[0] + lat[1]) / 2 to (lon[0] + lon[1]) / 2
    }
}
''', '''assertEquals("u4pruydqqvj", Geohash.encode(57.64911, 10.40744, 11))
        val (lat, lon) = Geohash.decode("u4pruydqqvj")
        assertEquals(57.64911, lat, 0.0001)
        assertEquals(10.40744, lon, 0.0001)''')

algo("point_in_polygon", "Ponto dentro de area (poligono)", GRAPH,
     "Verifica se uma coordenada esta dentro de uma area de entrega ou cerca virtual.", "PolygonArea", r'''
/** Algoritmos de poligonos em coordenadas planas (x = longitude, y = latitude). */
object PolygonArea {
    /** Ray casting: conta quantas arestas um raio horizontal cruza. */
    fun contains(polygon: List<Pair<Double, Double>>, x: Double, y: Double): Boolean {
        var inside = false
        var j = polygon.size - 1
        for (i in polygon.indices) {
            val (xi, yi) = polygon[i]
            val (xj, yj) = polygon[j]
            if ((yi > y) != (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) inside = !inside
            j = i
        }
        return inside
    }

    /** Area pela formula do laco (shoelace), em unidades ao quadrado. */
    fun area(polygon: List<Pair<Double, Double>>): Double {
        var sum = 0.0
        for (i in polygon.indices) {
            val (x1, y1) = polygon[i]
            val (x2, y2) = polygon[(i + 1) % polygon.size]
            sum += x1 * y2 - x2 * y1
        }
        return kotlin.math.abs(sum) / 2
    }
}
''', '''val square = listOf(0.0 to 0.0, 4.0 to 0.0, 4.0 to 4.0, 0.0 to 4.0)
        assertTrue(PolygonArea.contains(square, 2.0, 2.0))
        assertFalse(PolygonArea.contains(square, 5.0, 2.0))
        assertEquals(16.0, PolygonArea.area(square), 1e-9)''')

algo("douglas_peucker", "Simplificar trajeto (Douglas-Peucker)", GRAPH,
     "Reduz a quantidade de pontos de uma rota mantendo o formato, ideal para mapas e GPS.", "PathSimplifier", r'''
import kotlin.math.abs
import kotlin.math.hypot

/** Simplificacao de linhas pelo algoritmo de Ramer-Douglas-Peucker. */
object PathSimplifier {
    fun simplify(points: List<Pair<Double, Double>>, tolerance: Double): List<Pair<Double, Double>> {
        if (points.size < 3) return points
        var maxDistance = 0.0
        var index = 0
        val first = points.first()
        val last = points.last()
        for (i in 1 until points.size - 1) {
            val d = distance(points[i], first, last)
            if (d > maxDistance) {
                maxDistance = d
                index = i
            }
        }
        if (maxDistance <= tolerance) return listOf(first, last)
        val left = simplify(points.subList(0, index + 1), tolerance)
        val right = simplify(points.subList(index, points.size), tolerance)
        return left.dropLast(1) + right
    }

    // Distancia perpendicular do ponto p a reta ab.
    private fun distance(p: Pair<Double, Double>, a: Pair<Double, Double>, b: Pair<Double, Double>): Double {
        val dx = b.first - a.first
        val dy = b.second - a.second
        val length = hypot(dx, dy)
        if (length == 0.0) return hypot(p.first - a.first, p.second - a.second)
        return abs(dy * p.first - dx * p.second + b.first * a.second - b.second * a.first) / length
    }
}
''', '''val line = listOf(0.0 to 0.0, 1.0 to 0.01, 2.0 to -0.01, 3.0 to 5.0, 4.0 to 6.0, 5.0 to 7.0)
        val simple = PathSimplifier.simplify(line, 0.5)
        assertTrue(simple.size < line.size)
        assertEquals(line.first(), simple.first())
        assertEquals(line.last(), simple.last())''')

algo("price_rules", "Descontos, cupons e impostos", FIN,
     "Aplica desconto percentual ou fixo, faixas por quantidade e imposto sobre o preco.", "PriceRules", r'''
/** Regras de preco em centavos (Long) para evitar erros de arredondamento. */
object PriceRules {
    fun percentOff(cents: Long, percent: Double): Long = Math.round(cents * (1 - percent / 100.0))

    fun fixedOff(cents: Long, offCents: Long): Long = (cents - offCents).coerceAtLeast(0)

    /** Desconto por quantidade: [tiers] mapeia quantidade minima para percentual. */
    fun tierPercent(quantity: Int, tiers: Map<Int, Double>): Double =
        tiers.filterKeys { quantity >= it }.maxByOrNull { it.key }?.value ?: 0.0

    /** Imposto "por fora" (somado ao preco). */
    fun addTax(cents: Long, taxPercent: Double): Long = Math.round(cents * (1 + taxPercent / 100.0))

    /** Valor do imposto ja incluso no preco ("por dentro"). */
    fun includedTax(cents: Long, taxPercent: Double): Long = Math.round(cents - cents / (1 + taxPercent / 100.0))

    /** Aplica um cupom no formato "10%" ou "15.00" (valor fixo). */
    fun applyCoupon(cents: Long, coupon: String): Long {
        val text = coupon.trim().replace(",", ".")
        return if (text.endsWith("%")) {
            percentOff(cents, text.dropLast(1).toDoubleOrNull() ?: 0.0)
        } else {
            fixedOff(cents, Math.round((text.toDoubleOrNull() ?: 0.0) * 100))
        }
    }
}
''', '''assertEquals(9000L, PriceRules.percentOff(10000, 10.0))
        assertEquals(8500L, PriceRules.applyCoupon(10000, "15,00"))
        assertEquals(9000L, PriceRules.applyCoupon(10000, "10%"))
        assertEquals(10.0, PriceRules.tierPercent(12, mapOf(5 to 5.0, 10 to 10.0)), 1e-9)
        assertEquals(12300L, PriceRules.addTax(10000, 23.0))
        assertEquals(2300L, PriceRules.includedTax(12300, 23.0))''')

algo("business_metrics", "Ponto de equilibrio, ROI e payback", FIN,
     "Indicadores para pequenos negocios: margem, ponto de equilibrio, ROI e tempo de retorno.", "BusinessMetrics", r'''
import kotlin.math.ceil

/** Indicadores financeiros simples. */
object BusinessMetrics {
    /** Margem de contribuicao por unidade. */
    fun unitMargin(price: Double, variableCost: Double): Double = price - variableCost

    /** Unidades necessarias para cobrir os custos fixos. */
    fun breakEvenUnits(fixedCosts: Double, price: Double, variableCost: Double): Int {
        val margin = unitMargin(price, variableCost)
        require(margin > 0) { "O preco precisa ser maior que o custo variavel" }
        return ceil(fixedCosts / margin).toInt()
    }

    /** Retorno sobre investimento em percentual. */
    fun roi(gain: Double, cost: Double): Double = (gain - cost) / cost * 100

    /** Meses para recuperar o investimento com um lucro mensal constante. */
    fun paybackMonths(investment: Double, monthlyProfit: Double): Int =
        if (monthlyProfit <= 0) Int.MAX_VALUE else ceil(investment / monthlyProfit).toInt()

    /** Markup a aplicar sobre o custo para atingir a margem desejada (percentual). */
    fun markupForMargin(marginPercent: Double): Double = marginPercent / (100 - marginPercent) * 100
}
''', '''assertEquals(100, BusinessMetrics.breakEvenUnits(5000.0, 80.0, 30.0))
        assertEquals(50.0, BusinessMetrics.roi(1500.0, 1000.0), 1e-9)
        assertEquals(4, BusinessMetrics.paybackMonths(10000.0, 3000.0))
        assertEquals(100.0, BusinessMetrics.markupForMargin(50.0), 1e-9)''')

algo("inventory", "Estoque: lote economico e ponto de pedido", FIN,
     "Quanto e quando comprar: lote economico (EOQ), estoque de seguranca e ponto de reposicao.", "InventoryPlanner", r'''
import kotlin.math.ceil
import kotlin.math.sqrt

/** Planejamento de estoque. */
object InventoryPlanner {
    /** Lote economico de compra: demanda anual, custo por pedido e custo anual de manter uma unidade. */
    fun economicOrderQuantity(annualDemand: Double, orderCost: Double, holdingCost: Double): Int =
        ceil(sqrt(2 * annualDemand * orderCost / holdingCost)).toInt()

    /** Quantidade em estoque que dispara um novo pedido. */
    fun reorderPoint(dailyDemand: Double, leadTimeDays: Int, safetyStock: Int = 0): Int =
        ceil(dailyDemand * leadTimeDays).toInt() + safetyStock

    /** Estoque de seguranca simples: (demanda maxima - media) x prazo. */
    fun safetyStock(maxDailyDemand: Double, avgDailyDemand: Double, leadTimeDays: Int): Int =
        ceil((maxDailyDemand - avgDailyDemand) * leadTimeDays).toInt().coerceAtLeast(0)

    /** Dias que o estoque atual dura. */
    fun daysOfStock(current: Int, dailyDemand: Double): Double = if (dailyDemand <= 0) Double.POSITIVE_INFINITY else current / dailyDemand
}
''', '''assertEquals(400, InventoryPlanner.economicOrderQuantity(8000.0, 50.0, 5.0))
        assertEquals(60, InventoryPlanner.reorderPoint(10.0, 5, 10))
        assertEquals(25, InventoryPlanner.safetyStock(15.0, 10.0, 5))''')

algo("grades", "Media ponderada e notas", MATH,
     "Media ponderada, nota necessaria para aprovacao e conversao de percentuais em conceitos.", "Grades", r'''
/** Calculos de notas escolares. */
object Grades {
    fun weightedAverage(values: List<Double>, weights: List<Double>): Double {
        require(values.size == weights.size) { "Quantidade de notas e pesos deve ser igual" }
        val total = weights.sum()
        return if (total == 0.0) 0.0 else values.indices.sumOf { values[it] * weights[it] } / total
    }

    /** Nota minima na proxima avaliacao (peso [nextWeight]) para chegar em [target]. */
    fun neededGrade(values: List<Double>, weights: List<Double>, nextWeight: Double, target: Double): Double {
        val current = values.indices.sumOf { values[it] * weights[it] }
        return (target * (weights.sum() + nextWeight) - current) / nextWeight
    }

    /** Conceito A-E a partir do percentual. */
    fun letter(percent: Double): String = when {
        percent >= 90 -> "A"
        percent >= 80 -> "B"
        percent >= 70 -> "C"
        percent >= 60 -> "D"
        else -> "E"
    }
}
''', '''assertEquals(7.5, Grades.weightedAverage(listOf(6.0, 9.0), listOf(1.0, 1.0)), 1e-9)
        assertEquals(8.0, Grades.neededGrade(listOf(6.0), listOf(1.0), 1.0, 7.0), 1e-9)
        assertEquals("B", Grades.letter(85.0))''')

algo("streaks", "Sequencias de dias (streak)", UTIL,
     "Conta dias seguidos de uso, treino ou habito, e o recorde, a partir das datas registradas.", "Streaks", r'''
/** Sequencias de dias consecutivos. As datas sao dias desde 1970 (epochDay). */
object Streaks {
    /** Maior sequencia de dias seguidos. */
    fun best(days: Collection<Long>): Int {
        val sorted = days.toSortedSet()
        var best = 0
        var current = 0
        var previous: Long? = null
        for (day in sorted) {
            current = if (previous != null && day == previous + 1) current + 1 else 1
            best = maxOf(best, current)
            previous = day
        }
        return best
    }

    /** Sequencia atual terminando hoje (ou ontem, se hoje ainda nao foi registrado). */
    fun current(days: Collection<Long>, today: Long): Int {
        val set = days.toHashSet()
        var day = if (today in set) today else today - 1
        var count = 0
        while (day in set) {
            count++
            day--
        }
        return count
    }

    /** Converte milissegundos em epochDay no fuso informado. */
    fun epochDay(millis: Long, zoneOffsetMs: Long = java.util.TimeZone.getDefault().getOffset(millis).toLong()): Long =
        Math.floorDiv(millis + zoneOffsetMs, 86_400_000L)
}
''', '''val days = listOf(10L, 11L, 12L, 20L, 21L)
        assertEquals(3, Streaks.best(days))
        assertEquals(2, Streaks.current(days, 21L))
        assertEquals(2, Streaks.current(days, 22L))
        assertEquals(0, Streaks.current(days, 25L))
        assertEquals(1L, Streaks.epochDay(86_400_000L, 0))''')

algo("nps", "NPS (Net Promoter Score)", ML,
     "Calcula o NPS de pesquisas de satisfacao (notas de 0 a 10) e classifica as respostas.", "NetPromoterScore", r'''
/** Net Promoter Score: % promotores (9-10) menos % detratores (0-6). */
object NetPromoterScore {
    fun category(score: Int): String = when (score) {
        in 9..10 -> "Promotor"
        in 7..8 -> "Neutro"
        else -> "Detrator"
    }

    fun score(answers: List<Int>): Int {
        if (answers.isEmpty()) return 0
        val promoters = answers.count { it >= 9 }
        val detractors = answers.count { it <= 6 }
        return Math.round((promoters - detractors) * 100.0 / answers.size).toInt()
    }

    /** Zona do resultado segundo a escala usual. */
    fun zone(nps: Int): String = when {
        nps >= 75 -> "Excelencia"
        nps >= 50 -> "Qualidade"
        nps >= 0 -> "Aperfeicoamento"
        else -> "Critica"
    }
}
''', '''assertEquals(20, NetPromoterScore.score(listOf(10, 9, 8, 7, 3)))
        assertEquals("Neutro", NetPromoterScore.category(7))
        assertEquals("Qualidade", NetPromoterScore.zone(60))''')

algo("exercise_calories", "Calorias por exercicio (MET)", HEALTH,
     "Estima as calorias gastas por atividade usando a tabela MET (caminhada, corrida, bike...).", "ExerciseCalories", r'''
/** Gasto calorico estimado: kcal = MET x peso (kg) x horas. */
object ExerciseCalories {
    /** Valores MET aproximados (Compendium of Physical Activities). */
    val MET = mapOf(
        "caminhada" to 3.5,
        "caminhada rapida" to 5.0,
        "corrida" to 9.8,
        "bicicleta" to 7.5,
        "natacao" to 8.0,
        "musculacao" to 5.0,
        "yoga" to 2.5,
        "danca" to 5.5,
        "futebol" to 7.0
    )

    fun kcal(met: Double, weightKg: Double, minutes: Double): Double = met * weightKg * minutes / 60.0

    fun kcal(activity: String, weightKg: Double, minutes: Double): Double =
        kcal(MET[activity.lowercase()] ?: 4.0, weightKg, minutes)
}
''', '''assertEquals(245.0, ExerciseCalories.kcal(3.5, 70.0, 60.0), 1e-9)
        assertEquals(343.0, ExerciseCalories.kcal("corrida", 70.0, 30.0), 1e-9)''')

algo("running_pace", "Ritmo de corrida (pace)", HEALTH,
     "Pace por km, velocidade media e previsao de tempo em outra distancia (formula de Riegel).", "RunningPace", r'''
import kotlin.math.pow

/** Calculos de corrida. Tempos em segundos e distancias em km. */
object RunningPace {
    /** Segundos por km. */
    fun pace(seconds: Double, km: Double): Double = seconds / km

    /** Formata segundos como m:ss ou h:mm:ss. */
    fun format(seconds: Double): String {
        val total = Math.round(seconds)
        val h = total / 3600
        val m = (total % 3600) / 60
        val s = total % 60
        return if (h > 0) "%d:%02d:%02d".format(h, m, s) else "%d:%02d".format(m, s)
    }

    fun speedKmh(seconds: Double, km: Double): Double = km / (seconds / 3600.0)

    /** Previsao de tempo para [targetKm] a partir de uma prova feita (Riegel, expoente 1.06). */
    fun predict(seconds: Double, km: Double, targetKm: Double): Double = seconds * (targetKm / km).pow(1.06)
}
''', '''assertEquals("5:00", RunningPace.format(RunningPace.pace(1500.0, 5.0)))
        assertEquals(12.0, RunningPace.speedKmh(1500.0, 5.0), 1e-9)
        assertEquals("1:02:33", RunningPace.format(3753.0))
        assertTrue(RunningPace.predict(1500.0, 5.0, 10.0) > 3000.0)''')

algo("fitness_plan", "Gasto diario (TDEE) e macronutrientes", HEALTH,
     "Gasto energetico total pelo nivel de atividade e divisao de proteinas, carboidratos e gorduras.", "FitnessPlan", r'''
/** Plano nutricional simples. Nao substitui orientacao de nutricionista. */
object FitnessPlan {
    /** Fatores de atividade usuais. */
    val ACTIVITY = mapOf(
        "sedentario" to 1.2, "leve" to 1.375, "moderado" to 1.55, "intenso" to 1.725, "atleta" to 1.9
    )

    /** Gasto energetico total diario a partir da taxa basal. */
    fun tdee(bmr: Double, level: String): Double = bmr * (ACTIVITY[level] ?: 1.2)

    /** Meta calorica: deficit ou superavit percentual (negativo para emagrecer). */
    fun target(tdee: Double, adjustPercent: Double): Double = tdee * (1 + adjustPercent / 100.0)

    /** Gramas de (proteina, carboidrato, gordura) para as calorias e percentuais dados. */
    fun macros(kcal: Double, proteinPct: Double = 30.0, carbPct: Double = 40.0, fatPct: Double = 30.0): Triple<Int, Int, Int> =
        Triple(
            Math.round(kcal * proteinPct / 100 / 4).toInt(),
            Math.round(kcal * carbPct / 100 / 4).toInt(),
            Math.round(kcal * fatPct / 100 / 9).toInt()
        )
}
''', '''assertEquals(2325.0, FitnessPlan.tdee(1500.0, "moderado"), 1e-9)
        assertEquals(1800.0, FitnessPlan.target(2000.0, -10.0), 1e-9)
        assertEquals(Triple(150, 200, 67), FitnessPlan.macros(2000.0))''')

algo("depreciation", "Depreciacao de bens", FIN,
     "Valor de equipamentos e veiculos ao longo do tempo: linear e saldo decrescente.", "Depreciation", r'''
/** Depreciacao de ativos. */
object Depreciation {
    /** Valor contabil ao fim de cada ano, metodo linear. */
    fun straightLine(cost: Double, salvage: Double, years: Int): List<Double> {
        val perYear = (cost - salvage) / years
        return (1..years).map { cost - perYear * it }
    }

    /** Saldo decrescente com taxa anual [rate] (ex.: 0.2 = 20% ao ano), sem ficar abaixo do residual. */
    fun decliningBalance(cost: Double, rate: Double, years: Int, salvage: Double = 0.0): List<Double> {
        val values = mutableListOf<Double>()
        var value = cost
        repeat(years) {
            value = maxOf(salvage, value * (1 - rate))
            values.add(value)
        }
        return values
    }
}
''', '''assertEquals(listOf(8000.0, 6000.0, 4000.0), Depreciation.straightLine(10000.0, 4000.0, 3))
        assertEquals(6400.0, Depreciation.decliningBalance(10000.0, 0.2, 2).last(), 1e-9)''')

algo("sentiment_pt", "Analise de sentimento (portugues)", STR,
     "Classifica comentarios e avaliacoes como positivos, negativos ou neutros, sem internet.", "SentimentAnalyzer", r'''
/** Analise de sentimento por lexico, com tratamento simples de negacao e intensificadores. */
object SentimentAnalyzer {
    private val positive = setOf(
        "bom", "boa", "otimo", "otima", "excelente", "maravilhoso", "adorei", "amei", "gostei", "rapido",
        "perfeito", "recomendo", "lindo", "top", "eficiente", "pratico", "facil", "incrivel", "satisfeito", "feliz"
    )
    private val negative = setOf(
        "ruim", "pessimo", "pessima", "horrivel", "demorado", "lento", "odiei", "detestei", "caro", "quebrado",
        "atrasado", "problema", "defeito", "dificil", "nunca", "decepcionado", "frio", "errado", "sujo", "triste"
    )
    private val negations = setOf("nao", "nem", "jamais", "sem")
    private val boosters = setOf("muito", "super", "bastante", "demais", "extremamente")

    private fun normalize(text: String): List<String> {
        val map = mapOf('á' to 'a', 'à' to 'a', 'â' to 'a', 'ã' to 'a', 'é' to 'e', 'ê' to 'e', 'í' to 'i',
            'ó' to 'o', 'ô' to 'o', 'õ' to 'o', 'ú' to 'u', 'ç' to 'c')
        return text.lowercase().map { map[it] ?: it }.joinToString("")
            .split(Regex("[^a-z]+")).filter { it.isNotBlank() }
    }

    /** Pontuacao: positiva, negativa ou zero. */
    fun score(text: String): Double {
        val words = normalize(text)
        var total = 0.0
        for ((i, word) in words.withIndex()) {
            var value = when (word) {
                in positive -> 1.0
                in negative -> -1.0
                else -> continue
            }
            val window = words.subList(maxOf(0, i - 2), i)
            if (window.any { it in boosters }) value *= 1.5
            if (window.any { it in negations }) value = -value
            total += value
        }
        return total
    }

    fun label(text: String): String {
        val s = score(text)
        return when {
            s > 0 -> "positivo"
            s < 0 -> "negativo"
            else -> "neutro"
        }
    }
}
''', '''assertEquals("positivo", SentimentAnalyzer.label("Adorei, entrega muito rápida!"))
        assertEquals("negativo", SentimentAnalyzer.label("Não gostei, chegou atrasado"))
        assertEquals("neutro", SentimentAnalyzer.label("Chegou hoje"))''')

algo("keywords", "Palavras-chave de um texto", STR,
     "Extrai as palavras mais relevantes de um texto (frequencia sem palavras comuns), para tags e busca.",
     "KeywordExtractor", r'''
/** Extracao de palavras-chave por frequencia, ignorando palavras muito comuns em portugues. */
object KeywordExtractor {
    private val stopWords = setOf(
        "a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "por",
        "para", "com", "sem", "e", "ou", "que", "se", "nao", "mais", "muito", "como", "mas", "ao", "aos", "ja",
        "foi", "ser", "ter", "esta", "este", "isso", "isto", "eu", "voce", "ele", "ela", "seu", "sua", "meu", "minha",
        "the", "and", "of", "to", "in", "is", "it"
    )

    fun extract(text: String, limit: Int = 5, minLength: Int = 3): List<String> {
        val counts = linkedMapOf<String, Int>()
        text.lowercase().split(Regex("[^\\p{L}\\p{N}]+"))
            .filter { it.length >= minLength && it !in stopWords && it.toIntOrNull() == null }
            .forEach { counts[it] = (counts[it] ?: 0) + 1 }
        return counts.entries.sortedByDescending { it.value }.take(limit).map { it.key }
    }
}
''', '''val words = KeywordExtractor.extract("Pizza de calabresa. A pizza chegou quente e a calabresa estava boa. Pizza!", 2)
        assertEquals(listOf("pizza", "calabresa"), words)''')

algo("interpolation", "Interpolacao e escalas", MATH,
     "lerp, clamp e conversao entre escalas (ex.: 0-100 para 0-1), uteis em animacoes e graficos.", "Interpolation", r'''
/** Funcoes de interpolacao numerica. */
object Interpolation {
    fun lerp(start: Double, end: Double, t: Double): Double = start + (end - start) * t

    fun inverseLerp(start: Double, end: Double, value: Double): Double =
        if (end == start) 0.0 else (value - start) / (end - start)

    fun clamp(value: Double, min: Double, max: Double): Double = value.coerceIn(min, max)

    /** Converte [value] do intervalo [inMin, inMax] para [outMin, outMax]. */
    fun mapRange(value: Double, inMin: Double, inMax: Double, outMin: Double, outMax: Double): Double =
        lerp(outMin, outMax, inverseLerp(inMin, inMax, value))

    /** Suavizacao "ease in out" (smoothstep) para t entre 0 e 1. */
    fun smoothStep(t: Double): Double {
        val x = clamp(t, 0.0, 1.0)
        return x * x * (3 - 2 * x)
    }
}
''', '''assertEquals(5.0, Interpolation.lerp(0.0, 10.0, 0.5), 1e-9)
        assertEquals(0.25, Interpolation.inverseLerp(0.0, 100.0, 25.0), 1e-9)
        assertEquals(50.0, Interpolation.mapRange(0.5, 0.0, 1.0, 0.0, 100.0), 1e-9)
        assertEquals(0.5, Interpolation.smoothStep(0.5), 1e-9)''')

ALGORITHMS = {a.key: a for a in ALGORITHMS_LIST}

# Algoritmos que dependem de outros (para gerar os arquivos necessarios juntos).
ALGO_REQUIRES = {"tsp_nearest": ["haversine"]}


def by_category():
    groups = {}
    for a in ALGORITHMS_LIST:
        groups.setdefault(a.category, []).append(a)
    return groups
