#!/usr/bin/env python3
# This file is part of the ACTS project.
#
# Copyright (C) 2016 CERN for the benefit of the ACTS project
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
from pathlib import Path

import acts
from acts import MaterialMapJsonConverter
from acts.examples.odd import getOpenDataDetector
from acts.examples import (
    WhiteBoard,
    AlgorithmContext,
    ProcessCode,
    CsvTrackingGeometryWriter,
    ObjTrackingGeometryWriter,
    JsonSurfacesWriter,
    JsonMaterialWriter,
    JsonFormat,
)


def runGeometry(
    trackingGeometry: acts.TrackingGeometry,
    decorators,
    outputDir: Path,
    events: int = 1,
    outputObj: bool = True,
    outputCsv: bool = True,
    outputJson: bool = True,
):
    for ievt in range(events):
        eventStore = WhiteBoard(name=f"EventStore#{ievt}", level=acts.logging.INFO)
        ialg = 0

        context = AlgorithmContext(ialg, ievt, eventStore)

        for cdr in decorators:
            r = cdr.decorate(context)
            if r != ProcessCode.SUCCESS:
                raise RuntimeError("Failed to decorate event context")

        if outputCsv:
            csvPath = outputDir / "csv"
            if not csvPath.is_dir():
                csvPath.mkdir(parents=True)
            writer = CsvTrackingGeometryWriter(
                level=acts.logging.INFO,
                trackingGeometry=trackingGeometry,
                outputDir=csvPath,
                writePerEvent=True,
            )
            writer.write(context)

        if outputObj:
            objPath = outputDir / "obj"
            writer = ObjTrackingGeometryWriter(
                level=acts.logging.INFO,
                outputDir=objPath,
            )
            writer.write(context, trackingGeometry)

        if outputJson:
            jsonPath = outputDir / "json"
            if not jsonPath.is_dir():
                jsonPath.mkdir(parents=True)
            writer = JsonSurfacesWriter(
                level=acts.logging.INFO,
                trackingGeometry=trackingGeometry,
                outputDir=jsonPath,
                writePerEvent=True,
                writeSensitive=True,
            )
            writer.write(context)

            jmConverterCfg = MaterialMapJsonConverter.Config(
                processSensitives=True,
                processApproaches=True,
                processRepresenting=True,
                processBoundaries=True,
                processVolumes=True,
                processNonMaterial=True,
                context=context.geoContext,
            )

            jmw = JsonMaterialWriter(
                level=acts.logging.VERBOSE,
                converterCfg=jmConverterCfg,
                fileName=(outputDir / "geometry-map"),
                writeFormat=JsonFormat.Json,
            )

            jmw.write(trackingGeometry)


if "__main__" == __name__:
    # detector = AlignedDetector()
    # detector = GenericDetector()
    detector = getOpenDataDetector()
    trackingGeometry = detector.trackingGeometry()
    decorators = detector.contextDecorators()

    runGeometry(trackingGeometry, decorators, outputDir=Path.cwd())

    # Comment if you do not need to create the geometry id mapping for DD4hep
    dd4hepIdGeoIdMap = acts.examples.dd4hep.createDD4hepIdGeoIdMap(trackingGeometry)
    dd4hepIdGeoIdValueMap = {}
    for key, value in dd4hepIdGeoIdMap.items():
        dd4hepIdGeoIdValueMap[key] = value.value

    with open("odd-dd4hep-geoid-mapping.json", "w") as outfile:
        json.dump(dd4hepIdGeoIdValueMap, outfile)
