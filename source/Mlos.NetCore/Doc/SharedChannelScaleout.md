# Shared Channel Scaleout

Document contains results of the improvement in the shared communication channel.
We specifically address lack of the scalability issue. The channel does not scale well with increasing number of readers and
writers operating on the same channel instance.

## Benchmark

The benchmark is implemented in *Mlos.NetCore.Benchmark* project

Benchmark:
> $(MLOSROOT)\MLOS\out\obj\Source\Mlos.NetCore.Benchmark\obj\amd64\Mlos.NetCore.Benchmark.exe -i --filter SharedChannelReaderScaleOutBenchmarks

## Results

**Hyper-threading is disabled.**

---------------------------------------------------------------------------------------------------
### Intel E5-2670 v3 @ 2.30 GHz:

| ReaderCount |    Mean[B] |    Mean[I] | Error[B] | Error[I] | StdDev[B] | StdDev[I] | Allocated |
|------------:|-----------:|-----------:|---------:|---------:|----------:|----------:|----------:|
|           1 |   830.4 ms |   712.9 ms |  9.73 ms |  5.02 ms |   9.10 ms |   4.70 ms |    3584 B |
|           2 | 1,170.8 ms |   924.3 ms |  3.56 ms |  2.88 ms |   3.33 ms |   2.55 ms |    2104 B |
|           4 | 1,565.5 ms | 1,084.0 ms |  1.19 ms | 12.20 ms |   1.05 ms |  11.41 ms |    3856 B |
|           8 | 2,213.2 ms | 1,289.8 ms |  2.14 ms | 15.75 ms |   2.00 ms |  14.73 ms |    8048 B |
|          12 | 4,958.1 ms | 1,840.7 ms | 13.53 ms | 16.53 ms |  11.99 ms |  15.46 ms |   11216 B |
|          16 | 7,824.5 ms | 1,969.9 ms | 13.16 ms | 19.01 ms |  10.99 ms |  15.87 ms |   14944 B |
|          20 | 8,261.5 ms | 2,363.7 ms | 21.81 ms | 46.70 ms |  20.40 ms |  53.78 ms |   18576 B |
|          24 | 8,605.7 ms | 2,386.9 ms | 42.37 ms | 23.49 ms |  39.63 ms |  21.98 ms |   21376 B |



### Amd Ryzen 2700X
| ReaderCount |    Mean[B] |    Mean[I] | Error[B] | Error[I] | StdDev[B] | StdDev[I] | Allocated |
|------------ |-----------:|-----------:|---------:|---------:|----------:|----------:|----------:|
|           1 |   541.7 ms |   510.1 ms |  2.62 ms |  8.04 ms |   2.32 ms |   7.52 ms |    2856 B |
|           2 |   704.1 ms |   526.2 ms |  3.03 ms |  6.67 ms |   2.53 ms |   6.24 ms |    2064 B |
|           4 | 2,724.8 ms |   687.1 ms | 20.13 ms | 13.38 ms |  18.83 ms |  13.74 ms |    3856 B |
|           8 | 2,743.6 ms |   795.1 ms | 22.48 ms | 15.40 ms |  21.02 ms |  18.34 ms |    6616 B |


## Improvements

### Avoid creating proxies in the loop

Creating proxy classes (in this example .Sync and .ReadPosition) has a significant cost when the code is running in a tight loop. Before entering the loop, create a proxy structure and access it later inside the loop.

Example:
```C
      readPosition = buffer.Sync.ReadPosition.Load();
```

Is replaced with:

```C
   MLOSProxy.ChannelSynchronization sync = buffer.Sync;
   StdTypesProxy.AtomicUInt32 atomicReadPosition = sync.ReadPosition;
   ...
   int spinIndex = 0;
   while (true)
   {
      // Wait for the frame become available.
      // Spin on current frame (ReadOffset).
      //
      readPosition = atomicReadPosition.Load();
```

### StdAtomic

Removed MemoryBarrier and replaced with Volatile.Read and Volatile.Write.

```C
   readPosition = buffer.Sync.ReadPosition.Load();
...
   Interlocked.MemoryBarrier();
   return *(uint*)Buffer.ToPointer();
```

```asm
00007FFB118BC150 50                   push        rax
00007FFB118BC151 4C 8D 41 18          lea         r8,[rcx+18h]
00007FFB118BC155 49 8B C0             mov         rax,r8
00007FFB118BC158 48 8B 00             mov         rax,qword ptr [rax]
00007FFB118BC15B F0 83 0C 24 00     ->lock or     dword ptr [rsp],0
00007FFB118BC160 44 8B 08             mov         r9d,dword ptr [rax]
00007FFB118BC163 41 8B C1             mov         eax,r9d
```

```C      
   MLOSProxy.ChannelSynchronization sync = buffer.Sync;
   StdTypesProxy.AtomicUInt32 atomicReadPosition = sync.ReadPosition;
...
   readPosition = atomicReadPosition.Load();
...
   return Volatile.Read(ref *ptr);
```

```asm
   readPosition = atomicReadPosition.Load();
   00007FFDD883B005 48 8B C7             mov         rax,rdi  
   00007FFDD883B008 8B 28                mov         ebp,dword ptr [rax]  
   00007FFDD883B00A 8B C5                mov         eax,ebp  
```
