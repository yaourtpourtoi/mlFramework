from Reader import Reader

def main():

    channel = "tt"
    samples = "conf/global_config.json"

    read = Reader(channel = channel,
                  config_file = samples,
                  folds=2)

    numbers = {}
    targets = []
    for sample, sampleName in read.get(what = "nominal"):
        target =  read.config["target_names"][sample[0]["target"].iloc[0] ]

        numbers[ sampleName ] = {"total": len(sample[0]) + len(sample[1]) }
        numbers[ sampleName ]["evt"] = sample[0]["event_weight"].sum() + sample[1]["event_weight"].sum()


        if numbers.get(target, None) == None:
            numbers[target] = {"evt": sample[0]["event_weight"].sum() + sample[1]["event_weight"].sum() }
            numbers[target]["total"] = len(sample[0]) + len(sample[1])
            targets.append( target )
        else:
            numbers[target]["evt"] += sample[0]["event_weight"].sum() + sample[1]["event_weight"].sum()
            numbers[target]["total"] += len(sample[0]) + len(sample[1])
        

    total = 0.
    for n in numbers:
        if n in targets: continue
        total += numbers[n]["evt"]
    # print total
    for n in numbers:
        if n not in targets: continue

        print n, numbers[n]["total"] ,total / numbers[n]["evt"]



if __name__ == '__main__':
    main()
