# Web Data Paths Check

Status: PASS

Rules:
- web/src must not fetch root-absolute /projects or /data paths.
- web/src must not use root-absolute /projects or /data href values.
- Project data paths should go through withBasePath, projectDataPath, or projectsIndexPath.

No forbidden root-absolute data paths found.
