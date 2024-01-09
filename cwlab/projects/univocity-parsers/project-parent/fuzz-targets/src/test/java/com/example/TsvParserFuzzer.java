// Copyright 2023 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
////////////////////////////////////////////////////////////////////////////////

package com.example;

import com.code_intelligence.jazzer.api.FuzzedDataProvider;
import com.code_intelligence.jazzer.junit.FuzzTest;

import com.univocity.parsers.common.processor.*;
import com.univocity.parsers.common.TextParsingException;
import com.univocity.parsers.tsv.TsvParser;
import com.univocity.parsers.tsv.TsvParserSettings;

import java.io.Reader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.ByteArrayInputStream;


class TsvParserFuzzer {
    static RowProcessor [] rowProcessors = {new RowListProcessor(), new ObjectRowListProcessor(), new CompositeRowProcessor(), new ColumnProcessor(), new ObjectColumnProcessor()};

    @FuzzTest
    void myFuzzTest(FuzzedDataProvider data) {
        TsvParserSettings settings = new TsvParserSettings();

        settings.setRowProcessor(data.pickValue(rowProcessors));
        settings.setIgnoreLeadingWhitespaces(data.consumeBoolean());
        settings.setIgnoreTrailingWhitespaces(data.consumeBoolean());
        settings.setCommentCollectionEnabled(data.consumeBoolean());
        settings.setHeaderExtractionEnabled(data.consumeBoolean());
        settings.setAutoClosingEnabled(data.consumeBoolean());
        settings.setAutoConfigurationEnabled(data.consumeBoolean());
        settings.setColumnReorderingEnabled(data.consumeBoolean());
        settings.setLineJoiningEnabled(data.consumeBoolean());
        settings.setLineSeparatorDetectionEnabled(data.consumeBoolean());

        try (Reader inputReader = new InputStreamReader(new ByteArrayInputStream(data.consumeRemainingAsBytes()))) {
            TsvParser parser = new TsvParser(settings);
            parser.parseAll(inputReader);
            parser.parseAllRecords(inputReader);
            parser.parse(inputReader);
            parser.getContext();
            parser.getRecordMetadata();
            parser.getClass();
        } catch (IOException | TextParsingException e) {
        }
    }
}