using System;
using System.Diagnostics;
using System.Runtime;

namespace FinderScope.Core.Services
{
    /// <summary>
    /// パフォーマンス監視機能
    /// </summary>
    public class PerformanceMonitor
    {
        private readonly Stopwatch _stopwatch;
        private long _initialMemory;

        public PerformanceMonitor()
        {
            _stopwatch = new Stopwatch();
        }

        /// <summary>
        /// パフォーマンス測定を開始
        /// </summary>
        public void Start()
        {
            // ガベージコレクションを実行して正確なメモリ測定を行う
            GC.Collect();
            GC.WaitForPendingFinalizers();
            GC.Collect();

            _initialMemory = GC.GetTotalMemory(false);
            _stopwatch.Restart();
        }

        /// <summary>
        /// パフォーマンス測定を停止し、結果を取得
        /// </summary>
        public PerformanceResult Stop()
        {
            _stopwatch.Stop();
            
            var currentMemory = GC.GetTotalMemory(false);
            var memoryUsed = currentMemory - _initialMemory;

            return new PerformanceResult
            {
                ElapsedTime = _stopwatch.Elapsed,
                MemoryUsedBytes = memoryUsed,
                PeakWorkingSet = Environment.WorkingSet,
                ProcessorTimeUsed = Process.GetCurrentProcess().TotalProcessorTime
            };
        }

        /// <summary>
        /// メモリ最適化を実行
        /// </summary>
        public static void OptimizeMemory()
        {
            // ガベージコレクションを強制実行
            GC.Collect();
            GC.WaitForPendingFinalizers();
            GC.Collect();

            // LOH（Large Object Heap）の圧縮を試行
            GCSettings.LargeObjectHeapCompactionMode = GCLargeObjectHeapCompactionMode.CompactOnce;
            GC.Collect();
        }

        /// <summary>
        /// 現在のメモリ使用量を取得
        /// </summary>
        public static MemoryInfo GetCurrentMemoryInfo()
        {
            var process = Process.GetCurrentProcess();
            
            return new MemoryInfo
            {
                TotalAllocatedBytes = GC.GetTotalMemory(false),
                WorkingSetBytes = process.WorkingSet64,
                PrivateMemoryBytes = process.PrivateMemorySize64,
                VirtualMemoryBytes = process.VirtualMemorySize64,
                Gen0Collections = GC.CollectionCount(0),
                Gen1Collections = GC.CollectionCount(1),
                Gen2Collections = GC.CollectionCount(2)
            };
        }
    }

    /// <summary>
    /// パフォーマンス測定結果
    /// </summary>
    public class PerformanceResult
    {
        public TimeSpan ElapsedTime { get; set; }
        public long MemoryUsedBytes { get; set; }
        public long PeakWorkingSet { get; set; }
        public TimeSpan ProcessorTimeUsed { get; set; }

        public string MemoryUsedFormatted => FormatBytes(MemoryUsedBytes);
        public string PeakWorkingSetFormatted => FormatBytes(PeakWorkingSet);

        private static string FormatBytes(long bytes)
        {
            const long KB = 1024;
            const long MB = KB * 1024;
            const long GB = MB * 1024;

            return Math.Abs(bytes) switch
            {
                < KB => $"{bytes} B",
                < MB => $"{bytes / (double)KB:F1} KB",
                < GB => $"{bytes / (double)MB:F1} MB",
                _ => $"{bytes / (double)GB:F1} GB"
            };
        }

        public override string ToString()
        {
            return $"Time: {ElapsedTime.TotalMilliseconds:F2}ms, Memory: {MemoryUsedFormatted}, Peak Working Set: {PeakWorkingSetFormatted}";
        }
    }

    /// <summary>
    /// メモリ情報
    /// </summary>
    public class MemoryInfo
    {
        public long TotalAllocatedBytes { get; set; }
        public long WorkingSetBytes { get; set; }
        public long PrivateMemoryBytes { get; set; }
        public long VirtualMemoryBytes { get; set; }
        public int Gen0Collections { get; set; }
        public int Gen1Collections { get; set; }
        public int Gen2Collections { get; set; }

        public string TotalAllocatedFormatted => FormatBytes(TotalAllocatedBytes);
        public string WorkingSetFormatted => FormatBytes(WorkingSetBytes);
        public string PrivateMemoryFormatted => FormatBytes(PrivateMemoryBytes);

        private static string FormatBytes(long bytes)
        {
            const long KB = 1024;
            const long MB = KB * 1024;
            const long GB = MB * 1024;

            return bytes switch
            {
                < KB => $"{bytes} B",
                < MB => $"{bytes / (double)KB:F1} KB",
                < GB => $"{bytes / (double)MB:F1} MB",
                _ => $"{bytes / (double)GB:F1} GB"
            };
        }

        public override string ToString()
        {
            return $"Allocated: {TotalAllocatedFormatted}, Working Set: {WorkingSetFormatted}, " +
                   $"GC: Gen0={Gen0Collections}, Gen1={Gen1Collections}, Gen2={Gen2Collections}";
        }
    }
}