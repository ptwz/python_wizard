import logging

class LpcDecoder:
    """Decode LPC encoded data"""
    
    def __init__(self, tms_coeff, batch=False):
        self.bitpos = 0
        self.tables = tms_coeff
        self.batch = batch
    
    def rev_byte(self, byte):
        out_byte = 0
        for i in range(8):
            bit = (byte >> (7 - i)) & 1
            out_byte = out_byte | (bit << i)
        return out_byte
    
    def get_bits(self, bits):
        listpos = self.bitpos // 8
        bitpos = self.bitpos % 8
        try:
            databyte = self.rev_byte(self.data[listpos])
            if bitpos + bits + 1 > 8 and listpos + 1 < len(self.data):
                databyte = databyte << 8 | self.rev_byte(self.data[listpos + 1])
                ret_bits = (databyte >> (15 - (bitpos + bits) + 1)) & ((1 << bits) - 1)
                self.bitpos += bits
            else:
                ret_bits = (databyte >> abs(7 - (bitpos + bits) + 1)) & (abs(1 << bits) - 1)
                self.bitpos += bits
        except IndexError as e:
            print(e)
            print("no more bits error")
            return -1
        return ret_bits
    
    def decode(self, lpc_data):
        self.bitpos = 0
        self.data = lpc_data
        synth = {}
        target_synth = {}
        synth['K1'] = 0
        synth['K2'] = 0
        synth['K3'] = 0
        synth['K4'] = 0
        synth['K5'] = 0
        synth['K6'] = 0
        synth['K7'] = 0
        synth['K8'] = 0
        synth['K9'] = 0
        synth['K10'] = 0
        synth['period'] = 0
        synth['energy'] = 0
        for k in synth:
            target_synth[k] = synth[k]
        period_counter = 0
        frame_counter = 0
        
        x0 = x1 = x2 = x3 = x4 = x5 = x6 = x7 = x8 = x9 = x10 = 0
        
        samples = []
        logging.debug(f" Frame:NN - | Energy   | R | Pitch     | koeff")
        while True:
            debug_r=""
            debug_p=""
            debug_k=""
            
            energy = self.get_bits(self.tables.energy_bits)
            debug_e=f" {str(bin(energy))[2:].zfill(self.tables.energy_bits)}, {energy:<2} |"

            if energy == -1:
                break
            if energy == 0:
                target_synth['energy'] = 0
            elif energy == 0b1111:
                logging.debug(f" Frame:{frame_counter:2d} - | 1111, 15 |")
                break
            else:
                target_synth['energy'] = self.tables.energytable[energy]
                repeat = self.get_bits(1)
                debug_r=f" {repeat} |"
                period = self.get_bits(self.tables.pitch_bits)
                target_synth['period'] = self.tables.pitchtable[period]
                debug_p=f"{str(bin(period))[2:].zfill(self.tables.pitch_bits)}, {period:<2} |"
                debug_k=""
                if repeat == 0:
                    for k in range(10):
                        if period == 0 and k >= 4:
                            continue
                        k_bits=self.get_bits(self.tables.kbits[k])
                        target_synth[f"K{k + 1}"] = self.tables.ktable[k][k_bits]
                        debug_k+=f' {str(bin(k_bits))[2:].zfill(self.tables.kbits[k])}, {k_bits:>2} |'
            
            logging.debug(f" Frame:{frame_counter:2d} - |{debug_e}{debug_r}{debug_p}{debug_k}")

            if frame_counter == 0:
                # copy target to current keys
                for k in target_synth:
                    synth[k] = target_synth[k]
            
            interp_count = 0
            for sample_num in range(200):
                # interpolation time
                if interp_count == 0 and sample_num > 0:
                    interp_period = int(sample_num / 25)
                    for k in target_synth:
                        synth[k] += (target_synth[k] - synth[k]) >> self.tables.interp_coeff[interp_period]
                
                if synth['energy'] == 0:
                    u10 = 0
                elif synth['period'] > 0:
                    # Voiced frame
                    if period_counter < synth['period']:
                        period_counter += 1
                    else:
                        period_counter = 0
                    if period_counter < len(self.tables.chirptable):
                        u10 = int(self.tables.chirptable[period_counter] * synth['energy'] >> 6)
                    else:
                        u10 = 0
                else:
                    # Unvoiced
                    synthRand = 1
                    synthRand = (synthRand >> 1) ^ (0xB800 if synthRand & 1 else 0)
                    u10 = synth['energy'] if (synthRand & 1) else -synth['energy']
                
                # Lattice filter forward path
                u9 = u10 - int((synth['K10'] * x9) >> 9)
                u8 = u9 - int((synth['K9'] * x8) >> 9)
                u7 = u8 - int((synth['K8'] * x7) >> 9)
                u6 = u7 - int((synth['K7'] * x6) >> 9)
                u5 = u6 - int((synth['K6'] * x5) >> 9)
                u4 = u5 - int((synth['K5'] * x4) >> 9)
                u3 = u4 - int((synth['K4'] * x3) >> 9)
                u2 = u3 - int((synth['K3'] * x2) >> 9)
                u1 = u2 - int((synth['K2'] * x1) >> 9)
                u0 = u1 - int((synth['K1'] * x0) >> 9)
                
                # Output clamp
                if u0 > 511:
                    u0 = 511
                if u0 < -512:
                    u0 = -512
                
                # Lattice filter reverse path
                x9 = x8 + int((synth['K9'] * u8) >> 9)
                x8 = x7 + int((synth['K8'] * u7) >> 9)
                x7 = x6 + int((synth['K7'] * u6) >> 9)
                x6 = x5 + int((synth['K6'] * u5) >> 9)
                x5 = x4 + int((synth['K5'] * u4) >> 9)
                x4 = x3 + int((synth['K4'] * u3) >> 9)
                x3 = x2 + int((synth['K3'] * u2) >> 9)
                x2 = x1 + int((synth['K2'] * u1) >> 9)
                x1 = x0 + int((synth['K1'] * u0) >> 9)
                x0 = u0
                
                sample = (u0 >> 2) + 0x80
                samples.append(sample)
                interp_count = (interp_count + 1) % 25
            # return
            frame_counter += 1
        if self.batch:
            return (self.bitpos // 8) + 1
        else:
            return samples
