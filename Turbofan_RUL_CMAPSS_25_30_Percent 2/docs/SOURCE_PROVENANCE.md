# Source Provenance and Usage Note

## Identity

- Dataset: **Turbofan Engine Degradation Simulation Data Set (classic C-MAPSS FD001–FD004)**
- Provider/citation: A. Saxena and K. Goebel (2008), NASA Ames Prognostics Data Repository
- Official catalog: <https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data>
- NASA PCoE repository: <https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/>
- PHM Society NASA repository mirror used for retrieval: <https://data.phmsociety.org/nasa/>
- Retrieval date: 2026-09-02

The current NASA legacy ZIP endpoint timed out during packaging. The archive was therefore obtained from the PHM Society's NASA PCoE mirror, which identifies the data as the NASA Ames Turbofan Engine Degradation Simulation Data Set. No Kaggle or unofficially modified copy was used.

## Preserved archive

- File: `data/raw/source_archive/CMAPSSData.zip`
- SHA-256: `74bef434a34db25c7bf72e668ea4cd52afe5f2cf8e44367c55a82bfd91a5a34f`
- Contents: 12 FD001–FD004 train/test/RUL TXT files, original README, and the primary 2008 paper.

The extracted TXT/README files in `data/raw/files/` were independently compared byte-for-byte against this preserved ZIP after processing. All matched. Individual hashes are in `reports/checksums_sha256.txt`.

## Included primary paper

- File: `docs/Damage_Propagation_Modeling_2008.pdf`
- SHA-256: `e7aaef80c177333f400a4c1099fe76e67d244569b9397c937ec4cd3ed5b44a27`
- Citation: Saxena, A., Goebel, K., Simon, D., & Eklund, N. (2008). *Damage propagation modeling for aircraft engine run-to-failure simulation*. <https://doi.org/10.1109/PHM.2008.4711414>

## Interpretation and license note

The data are simulated C-MAPSS trajectories, not measurements from an operational airline fleet. The NASA Open Data resource currently lists the license as “not specified.” This package therefore does not invent or broaden a license; users should consult NASA's current catalog and terms before redistribution or commercial use. Academic reports should acknowledge the NASA Ames Prognostics Center of Excellence and the dataset authors.

