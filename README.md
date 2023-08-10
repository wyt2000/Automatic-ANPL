# Program-Synthetic-AutoTester
Evaluate the accurency of program synthesizers automatically by ChatGPT.    

## Overview

```
                               Program Snippets          Natural Language Descriptions
                                      +                               +
                                      |                               |
                                      |                               |
                                      |                               |
                                      |     +-----------------+       |
                                      |     |                 |       |
                                      +---->+ Program Sampler +<------+
                                            |                 |
                                            +--+-----------+--+
                                               |           |
                                               |           |
                                               |           |
                                 +-------------+           +-------------+
                                 |                                       |
              Synthesizer        |                                       |
              Description        v                                       v
                   +          Prompts                           I/O Specifications
                   |             +                                       +
                   |             |                                       |
                   |             v                                       |
                   |     +-------+--------+                              |
                   |     |                |                              |
                   +---> |    Wrapper     |                              |
                         |                |                              |
                         +-------+--------+                              |
                                 |                                       |
                                 |                                       |
                                 v                                       |
+------------+           +-------+--------+                              |
|            +---------> |                |                              |
|  ChatGPT   |           |   GPTClient    |                              |
|            | <---------+                |                              |
+------------+           +-------+--------+                              |
                                 |                                       |
                                 |                                       |
                                 v                                       |
                          Synthesizer's DSL                              |
                                 +                                       |
                                 |                                       |
                                 |                                       |
                                 v                                       |
                         +-------+--------+                              |
                         |                |                              |
                         |  Synthesizer   |                              |
                         |                |                              |
                         +-------+--------+                              |
                                 |                                       |
                                 |                                       |
                                 v                                       |
                           Target Programs                               |
                                 +                                       |
                                 |          +----------------+           |
                                 |          |                |           |
                                 +--------->+  Judge System  +<----------+
                                            |                |
                                            +-------+--------+
                                                    |
                                                    |
                                                    v
                                                 Accuracy
```

