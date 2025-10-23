
export type TPermission = {
    "module"? : {"C"?: number, "R"?: number, 'U'? : number, "D"?: number, 'V'?: number, "E"?: number},
    "sites_group"? : {"C"?: number, "R"?: number, 'U'? : number, "D"?: number, 'V'?: number, "E"?: number},
    "site"? : {"C"?: number, "R"?: number, 'U'? : number, "D"?: number, 'V'?: number, "E"?: number},
    "visit"?: { "C"?: number, "R"?: number, 'U'?: number, "D"?: number, 'V'?: number, "E"?: number },
    "observation"? : {"C"?: number, "R"?: number, 'U'? : number, "D"?: number, 'V'?: number, "E"?: number},
    "observation_detail"? : {"C"?: number, "R"?: number, 'U'? : number, "D"?: number, 'V'?: number, "E"?: number},
    "individual"?: { "C"?: number, "R"?: number, 'U'?: number, "D"?: number, 'V'?: number, "E"?: number },
    "marking"? : {"C"?: number, "R"?: number, 'U'? : number, "D"?: number, 'V'?: number, "E"?: number},
};
