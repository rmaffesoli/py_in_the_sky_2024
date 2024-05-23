import struct
import binascii
import contextlib

PACKAGE_FILE_TAG = 0x9E2A83C1
PACKAGE_FILE_TAG_SWAPPED = 0xC1832A9E
VER_UE4_OLDEST_LOADABLE_PACKAGE = 214
VER_UE4_WORLD_LEVEL_INFO = 224
VER_UE4_ADDED_CHUNKID_TO_ASSETDATA_AND_UPACKAGE = 278
VER_UE4_CHANGED_CHUNKID_TO_BE_AN_ARRAY_OF_CHUNKIDS = 326
VER_UE4_ENGINE_VERSION_OBJECT = 336
VER_UE4_ADD_STRING_ASSET_REFERENCES_MAP = 384
VER_UE4_PACKAGE_SUMMARY_HAS_COMPATIBLE_ENGINE_VERSION = 444
VER_UE4_SERIALIZE_TEXT_IN_PACKAGES = 459
VER_UE4_PRELOAD_DEPENDENCIES_IN_COOKED_EXPORTS = 507
VER_UE4_ADDED_SEARCHABLE_NAMES = 510
VER_UE4_ADDED_PACKAGE_SUMMARY_LOCALIZATION_ID = 516
VER_UE4_ADDED_PACKAGE_OWNER = 518
VER_UE4_NON_OUTER_PACKAGE_IMPORT = 520
VER_UE5_NAMES_REFERENCED_FROM_EXPORT_DATA = 1001
VER_UE5_PAYLOAD_TOC = 1002
VER_UE5_OPTIONAL_RESOURCES = 1003
VER_UE5_ADD_SOFTOBJECTPATH_LIST = 1008
VER_UE5_DATA_RESOURCES = 1009


class UassetReader:
    def __init__(self, uasset_file):
        self.uasset_file = uasset_file
        self.use_little_endian = True
        self.header = {}

        with contextlib.closing(open(self.uasset_file, "rb")) as self.file_obj:
            self.read_header()
            self.read_names()
            self.read_gatherable_text_data()
            self.read_imports()
            self.read_exports()
            self.read_dependencies()
            self.read_soft_package_references()
            self.read_searchable_names()
            self.read_thumbnails()
            self.read_asset_registry_data()
            self.read_preload_dependencies()
            self.read_bulk_data_start()

    @property
    def current_index(self):
        return self.file_obj.tell()

    def read_int16(self):
        return struct.unpack(
            "<h" if self.use_little_endian else ">h", self.file_obj.read(2)
        )[0]

    def read_uint16(self):
        return struct.unpack(
            "<H" if self.use_little_endian else ">H", self.file_obj.read(2)
        )[0]

    def read_int32(self):
        return struct.unpack(
            "<i" if self.use_little_endian else ">i", self.file_obj.read(4)
        )[0]

    def read_uint32(self):
        return struct.unpack(
            "<I" if self.use_little_endian else ">I", self.file_obj.read(4)
        )[0]

    def read_int64(self):
        return struct.unpack(
            "<q" if self.use_little_endian else ">q", self.file_obj.read(8)
        )[0]

    def read_uint64(self):
        return struct.unpack(
            "<Q" if self.use_little_endian else ">Q", self.file_obj.read(8)
        )[0]

    def read_fguidString(self):
        return binascii.hexlify(self.file_obj.read(16)).decode("utf-8").zfill(2)

    def read_fguidSlot(self):
        str1 = ""
        str2 = ""
        str3 = ""
        str4 = ""
        bytes = self.file_obj.read(16)

        for idx in range(3, -1, -1):
            str1 += "{:02x}".format(bytes[idx])
            str2 += "{:02x}".format(bytes[idx + 4])
            str3 += "{:02x}".format(bytes[idx + 8])
            str4 += "{:02x}".format(bytes[idx + 12])

        val = (str1 + str2 + str3 + str4).upper()

        return val

    def read_fstring(self):
        length = self.read_int32()
        if length == 0:
            return ""

        if length > 0:
            string_bytes = self.file_obj.read(length)
            string_bytes = string_bytes[:-1]  # remove null terminator
        string = string_bytes.decode(
            "utf-8"
        )  # assuming the string is in utf-8 encoding

        return string

    def read_header(self):
        self.header = {}
        self.header["EPackageFileTag"] = self.read_uint32()
        if self.header["EPackageFileTag"] == PACKAGE_FILE_TAG_SWAPPED:
            self.use_little_endian = False

        if (
            self.header["EPackageFileTag"] != PACKAGE_FILE_TAG
            and self.header["EPackageFileTag"] != PACKAGE_FILE_TAG_SWAPPED
        ):
            raise Exception("Invalid uasset")

        self.header["LegacyFileVersion"] = self.read_int32()
        if (
            self.header["LegacyFileVersion"] != -6
            and self.header["LegacyFileVersion"] != -7
            and self.header["LegacyFileVersion"] != -8
        ):
            raise Exception("Unsupported Version")

        self.header["LegacyUE3Version"] = self.read_int32()
        self.header["FileVersionUE4"] = self.read_int32()
        if self.header["LegacyFileVersion"] <= -8:
            self.header["FileVersionUE5"] = self.read_int32()

        self.header["FileVersionLicenseeUE4"] = self.read_int32()
        if (
            self.header["FileVersionUE4"] == 0
            and self.header["FileVersionLicenseeUE4"] == 0
            and self.header["FileVersionUE5"] == 0
        ):
            raise Exception("Asset unversioned")

        custom_version_count = self.read_int32()
        self.header["CustomVersions"] = []
        for _ in range(custom_version_count):
            key = self.read_fguidSlot()
            version = self.read_int32()
            self.header["CustomVersions"].append({key: version})

        self.header["TotalHeaderSize"] = self.read_int32()
        self.header["FolderName"] = self.read_fstring()
        self.header["PackageFlags"] = self.read_uint32()
        self.header["NameCount"] = self.read_int32()
        self.header["NameOffset"] = self.read_int32()

        if self.header["FileVersionUE5"] >= VER_UE5_ADD_SOFTOBJECTPATH_LIST:
            self.header["SoftObjectPathsCount"] = self.read_uint32()
            self.header["SoftObjectPathsOffset"] = self.read_uint32()

        if (
            self.header["FileVersionUE4"]
            >= VER_UE4_ADDED_PACKAGE_SUMMARY_LOCALIZATION_ID
        ):
            self.header["LocalizationId"] = self.read_fstring()

        if self.header["FileVersionUE4"] >= VER_UE4_SERIALIZE_TEXT_IN_PACKAGES:
            self.header["GatherableTextDataCount"] = self.read_int32()
            self.header["GatherableTextDataOffset"] = self.read_int32()

        self.header["ExportCount"] = self.read_int32()
        self.header["ExportOffset"] = self.read_int32()
        self.header["ImportCount"] = self.read_int32()
        self.header["ImportOffset"] = self.read_int32()
        self.header["DependsOffset"] = self.read_int32()

        if self.header["FileVersionUE4"] < VER_UE4_OLDEST_LOADABLE_PACKAGE:
            raise Exception("Asset too old")

        if self.header["FileVersionUE4"] >= VER_UE4_ADD_STRING_ASSET_REFERENCES_MAP:
            self.header["SoftPackageReferencesCount"] = self.read_int32()
            self.header["SoftPackageReferencesOffset"] = self.read_int32()

        if self.header["FileVersionUE4"] >= VER_UE4_ADDED_SEARCHABLE_NAMES:
            self.header["SearchableNamesOffset"] = self.read_int32()

        self.header["ThumbnailTableOffset"] = self.read_int32()
        self.header["Guid"] = self.read_fguidString()

        if self.header["FileVersionUE4"] >= VER_UE4_ADDED_PACKAGE_OWNER:
            self.header["PersistentGuid"] = self.read_fguidString()

        if (
            self.header["FileVersionUE4"] >= VER_UE4_ADDED_PACKAGE_OWNER
            and self.header["FileVersionUE4"] < VER_UE4_NON_OUTER_PACKAGE_IMPORT
        ):
            self.header["OwnerPersistentGuid"] = self.read_fguidString()

        count = self.read_int32()
        self.header["Generations"] = []
        for _ in range(count):
            export_count = self.read_int32()
            name_count = self.read_int32()
            self.header["Generations"].append(
                {"ExportCount": export_count, "NameCount": name_count}
            )

        if self.header["FileVersionUE4"] >= VER_UE4_ENGINE_VERSION_OBJECT:
            self.header["SavedByEngineVersion"] = (
                f"{self.read_uint16()}.{self.read_uint16()}.{self.read_uint16()}-{self.read_uint32()}+{self.read_fstring()}"
            )
        else:
            self.header["EngineChangeList"] = self.read_int32()

        if (
            self.header["FileVersionUE4"]
            >= VER_UE4_PACKAGE_SUMMARY_HAS_COMPATIBLE_ENGINE_VERSION
        ):
            self.header["CompatibleWithEngineVersion"] = (
                f"{self.read_uint16()}.{self.read_uint16()}.{self.read_uint16()}-{self.read_uint32()}+{self.read_fstring()}"
            )
        else:
            self.header["CompatibleWithEngineVersion"] = self.header[
                "SavedByEngineVersion"
            ]

        self.header["CompressionFlags"] = self.read_uint32()

        compressed_chunk_count = self.read_int32()
        if compressed_chunk_count > 0:
            raise Exception("Compressed assets not supported")

        self.header["PackageSource"] = self.read_uint32()

        packages_to_cook_count = self.read_uint32()
        if packages_to_cook_count > 0:
            raise Exception("Packages to cook in assets not supported")

        if self.header["LegacyFileVersion"] > -7:
            self.header["NumTextureAllocations"] = self.read_int32()

        self.header["AssetRegistryDataOffset"] = self.read_int32()
        self.header["BulkDataStartOffset"] = self.read_int64()

        if self.header["FileVersionUE4"] >= VER_UE4_WORLD_LEVEL_INFO:
            self.header["WorldTileInfoDataOffset"] = self.read_int32()

        if (
            self.header["FileVersionUE4"]
            >= VER_UE4_CHANGED_CHUNKID_TO_BE_AN_ARRAY_OF_CHUNKIDS
        ):
            chunk_id_count = self.read_int32()
            if chunk_id_count > 0:
                raise Exception("ChunkIDs has items")
        elif (
            self.header["FileVersionUE4"]
            >= VER_UE4_ADDED_CHUNKID_TO_ASSETDATA_AND_UPACKAGE
        ):
            self.header["ChunkID"] = self.read_int32()

        if (
            self.header["FileVersionUE4"]
            >= VER_UE4_PRELOAD_DEPENDENCIES_IN_COOKED_EXPORTS
        ):
            self.header["PreloadDependencyCount"] = self.read_int32()
            self.header["PreloadDependencyOffset"] = self.read_int32()
        else:
            self.header["PreloadDependencyCount"] = -1
            self.header["PreloadDependencyOffset"] = 0

        if self.header["FileVersionUE5"] >= VER_UE5_NAMES_REFERENCED_FROM_EXPORT_DATA:
            self.header["NamesReferencedFromExportDataCount"] = self.read_int32()

        if self.header["FileVersionUE5"] >= VER_UE5_PAYLOAD_TOC:
            self.header["PayloadTocOffset"] = self.read_int64()
        else:
            self.header["PayloadTocOffset"] = -1

        if self.header["FileVersionUE5"] >= VER_UE5_DATA_RESOURCES:
            self.header["DataResourceOffset"] = self.read_int32()

    def read_names(self):
        self.file_obj.seek(self.header["NameOffset"])
        self.names = [
            {
                "Name": self.read_fstring(),
                "NonCasePreservingHash": self.read_uint16(),
                "CasePreservingHash": self.read_uint16(),
            }
            for _ in range(self.header["NameCount"])
        ]

    def read_gatherable_text_data(self):
        return
        # TODO: Not sure if anything interesting is here.
        self.file_obj.seek(self.header["GatherableTextDataOffset"])
        self.gatherable_text_data = []
        for _ in range(self.header["GatherableTextDataCount"]):
            text_data = {
                "NamespaceName": self.read_fstring(),
                "SourceData": {
                    "SourceString": self.read_fstring(),
                    "SourceStringMetaData": {
                        "ValueCount": self.read_int32(),
                        "Values": [],
                    },
                },
            }
            if text_data["SourceData"]["SourceStringMetadata"]["ValueCount"] > 0:
                print("unsupported SourceStringMetaData from readGatherableTextData")
                # raise Exception(
                #     "unsupported SourceStringMetaData from readGatherableTextData"
                # )

            text_data["SourceSiteContexts"] = []
            countSourceSiteContexts = self.read_int32()
            for _ in range(countSourceSiteContexts):
                text_data["SourceSiteContexts"].append(
                    {
                        "SiteContext": self.read_fstring(),
                        "SiteContextMetaData": {
                            "ValueCount": self.read_int32(),
                            "Values": [],
                        },
                    }
                )

        # TODO: Finish this method if it seems important

    def read_imports(self):
        return
        # TODO: Figure out why the indices are not being read correctly
        self.file_obj.seek(self.header["ImportOffset"])
        self.imports = []
        for _ in range(self.header["ImportCount"]):
            class_package = self.read_uint64()
            class_name = self.read_uint64()
            outer_index = self.read_int32()
            object_name = self.read_uint64()
            package_name = (
                self.read_uint64()
                if self.header["FileVersionUE4"] >= VER_UE4_NON_OUTER_PACKAGE_IMPORT
                else 0
            )
            b_import_optional = (
                (
                    self.read_int32()
                    if self.header["FileVersionUE4"] >= VER_UE5_OPTIONAL_RESOURCES
                    else 0
                ),
            )

            self.imports.append(
                {
                    "ClassPackage": self.find_name(class_package),
                    "ClassName": self.find_name(class_name),
                    "OuterIndex": outer_index,
                    "ObjectName": self.find_name(object_name),
                    "PackageName": self.find_name(package_name),
                    "bImportOptional": b_import_optional,
                }
            )

    def read_exports(self):
        pass

    def read_dependencies(self):
        pass

    def read_soft_package_references(self):
        pass

    def read_searchable_names(self):
        pass

    def read_thumbnails(self):
        self.file_obj.seek(self.header["ThumbnailTableOffset"])
        thumbnail_count = self.read_int32()
        self.thumbnails = []
        for _ in range(thumbnail_count):
            self.thumbnails.append(
                {
                    "AssetClassName": self.read_fstring(),
                    "ObjectPathWithoutPackageName": self.read_fstring(),
                    "FileOffset": self.read_int32(),
                }
            )

        for thumbnail in self.thumbnails:
            self.file_obj.seek(thumbnail["FileOffset"])
            thumbnail["Width"] = self.read_int32()
            thumbnail["Height"] = self.read_int32()
            thumbnail["Format"] = "JPEG" if thumbnail["Height"] < 0 else "PNG"
            thumbnail["Height"] = abs(thumbnail["Height"])
            thumbnail["Size"] = self.read_int32()
            thumbnail["Bytes"] = (
                self.file_obj.read(thumbnail["Size"]) if thumbnail["Size"] > 0 else None
            )

    def read_asset_registry_data(self):
        pass

    def read_preload_dependencies(self):
        pass

    def read_bulk_data_start(self):
        pass

    def find_name(self, index):
        return self.names[index]["Name"]


if __name__ == "__main__":
    reader = UassetReader("test_files/SM_Stairs.uasset")
    print(reader.header)
